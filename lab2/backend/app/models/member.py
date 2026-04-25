from sqlalchemy import Column, DateTime, Integer, String, Text, func
from app.db.session import Base


class Member(Base):
    __tablename__ = "members"

    member_id = Column(String(64), primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    headline = Column(String(255), nullable=True)
    about_summary = Column(Text, nullable=True)
    experience_json = Column(Text, nullable=True)
    education_json = Column(Text, nullable=True)
    skills_json = Column(Text, nullable=True)
    profile_photo_url = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    connections_count = Column(Integer, nullable=False, default=0)
    profile_views_daily = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
