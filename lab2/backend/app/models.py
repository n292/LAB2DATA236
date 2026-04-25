from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, Enum as SQLEnum, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class UserRole(str, enum.Enum):
    USER = "user"
    OWNER = "owner"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    about_me = Column(Text, nullable=True)
    city = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    state = Column(String(2), nullable=True)
    languages = Column(String(200), nullable=True)
    gender = Column(String(20), nullable=True)
    profile_picture = Column(LargeBinary, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    reviews = relationship("Review", back_populates="author", foreign_keys="Review.user_id")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    favorites = relationship("Favorite", back_populates="user")
    owned_restaurants = relationship("Restaurant", back_populates="owner")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    cuisines = Column(String(500), nullable=True)  # JSON string
    price_range = Column(String(50), nullable=True)
    preferred_location = Column(String(200), nullable=True)
    dietary_restrictions = Column(String(500), nullable=True)  # JSON string
    ambiance = Column(String(500), nullable=True)  # JSON string
    sort_preference = Column(String(50), nullable=True)
    search_radius = Column(Integer, default=5)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="preferences")


class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    cuisine_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=False)
    city = Column(String(50), nullable=False)
    zip_code = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    hours_of_operation = Column(String(500), nullable=True)  # JSON string
    amenities = Column(String(500), nullable=True)  # JSON string
    pricing_tier = Column(String(10), nullable=True)  # $, $$, $$$, $$$$
    photos = Column(LargeBinary, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    reviews = relationship("Review", back_populates="restaurant")
    favorites = relationship("Favorite", back_populates="restaurant")
    owner = relationship("User", back_populates="owned_restaurants")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    photos = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    author = relationship("User", back_populates="reviews", foreign_keys=[user_id])
    restaurant = relationship("Restaurant", back_populates="reviews")


class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="favorites")
    restaurant = relationship("Restaurant", back_populates="favorites")
