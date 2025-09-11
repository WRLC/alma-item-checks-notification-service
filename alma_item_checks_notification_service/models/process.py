"""Process model"""

from sqlalchemy import Column, Integer, String

from alma_item_checks_notification_service.models.base import Base


class Process(Base):
    """Process model"""

    __tablename__ = "process"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email_subject = Column(String(255), nullable=False)
    email_body = Column(String(255), nullable=False)
    email_addendum = Column(String(255), nullable=True)
    container = Column(String(255), nullable=False)
