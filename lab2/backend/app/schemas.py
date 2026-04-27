from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    USER = "user"
    OWNER = "owner"


# ============ Auth Schemas ============
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str


# ============ User Schemas ============
class UserPreferenceUpdate(BaseModel):
    cuisines: Optional[List[str]] = None
    price_range: Optional[str] = None
    preferred_location: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    ambiance: Optional[List[str]] = None
    sort_preference: Optional[str] = None
    search_radius: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None
    profile_photo_data: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None
    role: str
    created_at: datetime
    profile_photo_data: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Restaurant Schemas ============
class RestaurantCreate(BaseModel):
    name: str
    cuisine_type: str
    description: Optional[str] = None
    address: str
    city: str
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hours_of_operation: Optional[dict] = None
    amenities: Optional[List[str]] = None
    pricing_tier: Optional[str] = None
    photo_data: Optional[str] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hours_of_operation: Optional[dict] = None
    amenities: Optional[List[str]] = None
    pricing_tier: Optional[str] = None
    photo_data: Optional[str] = None


class RestaurantResponse(BaseModel):
    id: int
    name: str
    cuisine_type: str
    description: Optional[str] = None
    address: str
    city: str
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hours_of_operation: Optional[dict] = None
    amenities: Optional[list] = None
    pricing_tier: Optional[str] = None
    average_rating: float
    review_count: int
    created_at: datetime
    photo_data: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Review Schemas ============
class ReviewCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    author: Optional[UserResponse]

    class Config:
        from_attributes = True


# ============ AI Assistant Schemas ============
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = None


class RecommendationItem(BaseModel):
    id: int
    name: str
    rating: float
    price_tier: str
    cuisine_type: str
    reasoning: str


class ChatResponse(BaseModel):
    response: str
    recommendations: Optional[List[RecommendationItem]] = None


# ============ Favorite Schemas ============
class FavoriteCreate(BaseModel):
    restaurant_id: int


class FavoriteResponse(BaseModel):
    id: int
    restaurant_id: int
    created_at: datetime
    restaurant: Optional[RestaurantResponse]

    class Config:
        from_attributes = True