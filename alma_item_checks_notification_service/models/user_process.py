"""UserProcess model"""
from sqlalchemy import Column, Integer, ForeignKey

from alma_item_checks_notification_service.models.base import Base
from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.models.user import User


class UserProcess(Base):
    """UserProcess model"""
    __tablename__ = "user_process"

    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    process_id = Column(Integer, ForeignKey(Process.id), primary_key=True)
