"""User model"""
from sqlalchemy import Column, String, Integer

from alma_item_checks_notification_service.models.base import Base


class User(Base):
    """User model"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    institution_id = Column(Integer, unique=True, nullable=False)
