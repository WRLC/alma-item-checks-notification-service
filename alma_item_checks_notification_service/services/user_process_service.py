"""Service class for UserProcesses"""
from sqlalchemy.orm import Session

from alma_item_checks_notification_service.repos.user_process_repo import UserProcessRepository
from alma_item_checks_notification_service.services.process_service import ProcessService
from alma_item_checks_notification_service.services.user_service import UserService


class UserProcessService:
    """Service class for UserProcesses"""
    def __init__(self, session: Session):
        self.process_service = ProcessService(session)
        self.user_process_repo = UserProcessRepository(session)
        self.user_service = UserService(session)

    def get_user_emails_for_process(self, process_id: int, institution_id: int) -> list[str]:
        """Get all user emails for a given process type and institution id

        Args:
            process_id (int): id of the processor
            institution_id (int): Institution id

        Returns:
            list[str]: List of user emails or None
        """
        user_ids: list[int] | None = self.user_process_repo.get_users_for_process(process_id)

        if user_ids is None:
            return []

        user_emails: list[str] = []

        for user_id in user_ids:
            email: str | None = self.user_service.get_user_email(user_id, institution_id)
            if email:
                user_emails.append(email)

        return user_emails
