"""Repository for the UserProcess table"""
import logging

from sqlalchemy import Select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from alma_item_checks_notification_service.models.user_process import UserProcess


class UserProcessRepository:
    """Repository for the UserProcess table"""
    def __init__(self, session: Session):
        self.session = session

    def get_users_for_process(self, process_id: int) -> list[int] | None:
        """Get a list of user ids for a process type and institution id

        Args:
            process_id (int): Process ID

        Returns:
            list[str]: List of user ids or None
        """
        stmt: Select = Select(UserProcess).where(UserProcess.process_id == process_id)

        try:
            users: list[UserProcess] = list(self.session.execute(stmt).scalars().all())

            user_ids: list[int] = []

            for user in users:
                user_ids.append(int(user.user_id))

            return user_ids

        except NoResultFound:
            logging.error(f"UserProcessRepository.get_users_for_process: NoResultFound")
            return None
        except SQLAlchemyError as e:
            logging.error(f"UserProcessRepository.get_users_for_process: SQLAlchemyError: {e}")
            return None
        except Exception as e:
            logging.error(f"UserProcessRepository.get_users_for_process: Exception: {e}")
            return None
