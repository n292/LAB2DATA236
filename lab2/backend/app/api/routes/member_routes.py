from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.schemas.member import (
    MemberCreate,
    MemberDeleteRequest,
    MemberGetRequest,
    MemberResponse,
    MemberSearchRequest,
    MemberUpdate,
    PhotoUploadResponse,
)
from app.services.member_service import (
    create_member,
    delete_member,
    delete_photo_file,
    get_member,
    search_members,
    update_member,
)
from app.utils.kafka_envelope import build_event
from app.utils.kafka_producer import publish_event

router = APIRouter(prefix="/members", tags=["Members"])
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/create", response_model=MemberResponse)
def create_member_route(payload: MemberCreate, db: Session = Depends(get_db)):
    ok, message, member_id, member = create_member(db, payload)
    if not ok:
        return MemberResponse(success=False, message=message, error=message)

    event = build_event(
        event_type="member.created",
        actor_id=member_id,
        entity_type="member",
        entity_id=member_id,
        payload={
            "member_id": member_id,
            "email": payload.email,
            "headline": payload.headline,
            "city": payload.city,
            "state": payload.state,
            "country": payload.country,
            "skills": payload.skills,
        },
    )
    publish_event(settings.kafka_member_created_topic, event, key=member_id)
    return MemberResponse(success=True, message=message, member_id=member_id, member=member)


@router.post("/get", response_model=MemberResponse)
def get_member_route(payload: MemberGetRequest, db: Session = Depends(get_db)):
    member = get_member(db, payload.member_id)
    if not member:
        return MemberResponse(success=False, message="Member not found", error="Member not found")

    if payload.emit_profile_viewed:
        actor_id = payload.viewer_id or "anonymous"
        trace_id = str(uuid4())
        view_source = payload.view_source or "profile_page"

        event = build_event(
            event_type="profile.viewed",
            actor_id=actor_id,
            entity_type="member",
            entity_id=payload.member_id,
            payload={
                "profile_id": payload.member_id,
                "view_source": view_source,
                "route": f"/members/{payload.member_id}",
                "viewer_authenticated": payload.viewer_id is not None,
            },
            trace_id=trace_id,
            idempotency_key=f"profile-viewed:{actor_id}:{payload.member_id}:{trace_id}",
        )
        publish_event(settings.kafka_profile_viewed_topic, event, key=payload.member_id)

    return MemberResponse(success=True, message="Member fetched successfully", member=member)


@router.post("/update", response_model=MemberResponse)
def update_member_route(payload: MemberUpdate, db: Session = Depends(get_db)):
    old = get_member(db, payload.member_id)
    ok, message, member = update_member(db, payload)
    if not ok:
        return MemberResponse(success=False, message=message, error=message)

    event = build_event(
        event_type="member.updated",
        actor_id=payload.member_id,
        entity_type="member",
        entity_id=payload.member_id,
        payload={"before": old, "after": member},
    )
    publish_event(settings.kafka_member_updated_topic, event, key=payload.member_id)
    return MemberResponse(success=True, message=message, member_id=payload.member_id, member=member)


@router.post("/delete", response_model=MemberResponse)
def delete_member_route(payload: MemberDeleteRequest, db: Session = Depends(get_db)):
    member = get_member(db, payload.member_id)
    if not member:
        return MemberResponse(success=False, message="Member not found", error="Member not found")
    delete_photo_file(settings.upload_path, member.get("profile_photo_url"))
    ok = delete_member(db, payload.member_id)
    if not ok:
        return MemberResponse(success=False, message="Delete failed", error="Delete failed")
    return MemberResponse(success=True, message="Member deleted successfully", member_id=payload.member_id)


@router.post("/search", response_model=MemberResponse)
def search_members_route(payload: MemberSearchRequest, db: Session = Depends(get_db)):
    members = search_members(db, payload)
    return MemberResponse(success=True, message="Members fetched successfully", members=members)


@router.post("/upload-photo", response_model=PhotoUploadResponse)
async def upload_photo_route(
    request: Request,
    member_id: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return PhotoUploadResponse(
            success=False,
            message="Invalid file type",
            error="Allowed: jpg, jpeg, png, gif, webp",
        )

    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        return PhotoUploadResponse(
            success=False,
            message="File too large",
            error=f"Max size is {settings.max_file_size_mb} MB",
        )

    filename = f"photo_{uuid4().hex}{suffix}"
    output_path = settings.upload_path / filename
    output_path.write_bytes(content)
    photo_url = str(request.base_url).rstrip("/") + f"/uploads/{filename}"

    if member_id:
        existing = get_member(db, member_id)
        if not existing:
            output_path.unlink(missing_ok=True)
            return PhotoUploadResponse(success=False, message="Member not found", error="Member not found")
        delete_photo_file(settings.upload_path, existing.get("profile_photo_url"))
        ok, message, member = update_member(db, MemberUpdate(member_id=member_id, profile_photo_url=photo_url))
        if not ok:
            output_path.unlink(missing_ok=True)
            return PhotoUploadResponse(success=False, message=message, error=message)

        event = build_event(
            event_type="member.updated",
            actor_id=member_id,
            entity_type="member",
            entity_id=member_id,
            payload={"before": existing, "after": member, "updated_field": "profile_photo_url"},
        )
        publish_event(settings.kafka_member_updated_topic, event, key=member_id)

    return PhotoUploadResponse(
        success=True,
        message="Photo uploaded successfully",
        profile_photo_url=photo_url,
        filename=filename,
    )