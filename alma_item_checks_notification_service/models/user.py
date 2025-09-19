"""User model"""

from sqlalchemy import Column, String, Integer, UniqueConstraint

from alma_item_checks_notification_service.models.base import Base


class User(Base):
    """User model"""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    institution_id = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("email", "institution_id"),)
