from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from schemas import ChatRequest, ChatResponse
from database import get_db

from services.ai_service import process_chat_message

router = APIRouter(tags=["ai-assistant"])


def resolve_user(db: Session, user_id: Optional[int]) -> User:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id is required for loading user preferences"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.post("/api/ai-assistant/chat", response_model=ChatResponse)
def chat_with_assistant(
    chat_request: ChatRequest,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    - /api/ai-assistant/chat 
    """
    user = resolve_user(db, user_id)

    result = process_chat_message(
        user_message=chat_request.message,
        db=db,
        user_id=user.id,
        conversation_history=chat_request.conversation_history
    )

    return ChatResponse(
        response=result["response"],
        recommendations=result.get("recommendations", [])
    )