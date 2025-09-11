"""Service class for Processes"""

from sqlalchemy.orm import Session

from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.repos.process_repo import ProcessRepository


class ProcessService:
    """Service class for Processes"""

    def __init__(self, session: Session):
        self.process_repo = ProcessRepository(session)

    def get_process_id_by_name(self, process_type: str) -> int | None:
        """Get process id by name

        Args:
            process_type (str): process type

        Returns:
            int | None: process id or None
        """
        process_id: int | None = self.process_repo.get_process_id_by_name(process_type)

        return process_id

    def get_process_by_name(self, process_type: str) -> Process | None:
        """Get process object by name

        Args:
            process_type (str): process type

        Returns:
            Process | None: process object or None
        """
        process: Process | None = self.process_repo.get_process_by_name(process_type)

        return process
