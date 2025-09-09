"""Repository for the User table"""
import logging

from sqlalchemy import Select, and_
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from alma_item_checks_notification_service.models.user import User


class UserRepository:
    """Repository for the User table"""
    def __init__(self, session: Session):
        self.session = session

    def get_user_email(self, user_id: int, institution_id: int | None = None) -> str | None:
        """Get user email address from user id

        Args:
            user_id (str): user id
            institution_id (int): institution id or None

        Returns:
            str: user email address or None
        """
        stmt: Select

        if institution_id is not None:
            stmt = Select(User).where(and_(User.id == user_id, User.institution_id == institution_id))
        else:
            stmt = Select(User).where(User.id == user_id)

        try:
            user: User | None = self.session.execute(stmt).scalar_one_or_none()

            if user is None or user.email is None:
                logging.error(f"User {user_id} not found")
                return None

            return str(user.email)

        except NoResultFound:
            logging.error("UserRepository::get_user_email(): user not found")
            return None
        except SQLAlchemyError as e:
            logging.error(f"UserRepository::get_user_email(): {e}")
            return None
        except Exception as e:
            logging.error(f"UserRepository::get_user_email(): {e}")
            return None