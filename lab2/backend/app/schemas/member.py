from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class MemberBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    headline: Optional[str] = None
    about_summary: Optional[str] = None
    experience: List[dict] = []
    education: List[dict] = []
    skills: List[str] = []
    profile_photo_url: Optional[str] = None
    resume_text: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberGetRequest(BaseModel):
    member_id: str
    viewer_id: Optional[str] = None
    emit_profile_viewed: bool = False
    view_source: Optional[str] = None


class MemberUpdate(BaseModel):
    member_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    headline: Optional[str] = None
    about_summary: Optional[str] = None
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    skills: Optional[List[str]] = None
    profile_photo_url: Optional[str] = None
    resume_text: Optional[str] = None


class MemberDeleteRequest(BaseModel):
    member_id: str


class MemberSearchRequest(BaseModel):
    skill: Optional[str] = None
    location: Optional[str] = None
    keyword: Optional[str] = None


class MemberResponse(BaseModel):
    success: bool
    message: str
    member_id: Optional[str] = None
    member: Optional[dict] = None
    members: Optional[list] = None
    error: Optional[str] = None


class PhotoUploadResponse(BaseModel):
    success: bool
    message: str
    profile_photo_url: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None