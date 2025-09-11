"""Repository for the user_process table"""

import logging

from sqlalchemy import Select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from alma_item_checks_notification_service.models.process import Process


class ProcessRepository:
    """Repository for the process table"""

    def __init__(self, session: Session):
        self.session = session

    def get_process_by_name(self, process_name: str) -> Process | None:
        """Get process by name

        Args:
            process_name (str): name of the process to get

        Returns:
            Process | None: process object or None
        """
        stmt: Select = Select(Process).where(Process.name == process_name)

        try:
            process: Process | None = self.session.execute(stmt).scalars().first()

            if not process:
                logging.error(
                    f"ProcessRepository::get_process_by_name: {process_name} not found"
                )

            return process

        except NoResultFound:
            logging.error(
                f"ProcessRepository.get_process_id_by_name: No process found with name '{process_name}'"
            )
            return None
        except SQLAlchemyError as e:
            logging.error(
                f"ProcessRepository.get_process_id_by_name: SQLAlchemyError: {e}"
            )
            return None
        except Exception as e:
            logging.error(f"ProcessRepository.get_process_id_by_name: Exception: {e}")
            return None

    def get_process_id_by_name(self, name: str) -> int | None:
        """Get process id by name

        Args:
            name (str): name of the process

        Returns:
            int | None: process id or None
        """
        stmt: Select = Select(Process).where(Process.name == name)

        try:
            process: Process | None = self.session.execute(stmt).scalars().first()

            if not process:
                logging.error(
                    f"ProcessRepository.get_process_id_by_name: Process '{name}' not found"
                )
                return None

            return int(process.id)

        except NoResultFound:
            logging.error(
                f"ProcessRepository.get_process_id_by_name: No process found with name '{name}'"
            )
            return None
        except SQLAlchemyError as e:
            logging.error(
                f"ProcessRepository.get_process_id_by_name: SQLAlchemyError: {e}"
            )
            return None
        except Exception as e:
            logging.error(f"ProcessRepository.get_process_id_by_name: Exception: {e}")
            return None
