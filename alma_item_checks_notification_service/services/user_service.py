"""Service class for Users"""
from sqlalchemy.orm import Session

from alma_item_checks_notification_service.repos.user_repo import UserRepository


class UserService:
    """Service class for Users"""
    def __init__(self, session: Session):
        self.user_repo = UserRepository(session)

    def get_user_email(self, user_id: int, institution_id: int) -> str | None:
        """Gets user email from user id

        Args:
            user_id (int): user id
            institution_id (int): institution id

        Returns:
            str | None: user email address or None
        """
        user_email: str | None = self.user_repo.get_user_email(user_id, institution_id)

        return user_email
