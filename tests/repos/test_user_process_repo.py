"""Tests for UserProcessRepository"""

from unittest.mock import patch
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from alma_item_checks_notification_service.models.user import User
from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.models.user_process import UserProcess
from alma_item_checks_notification_service.repos.user_process_repo import (
    UserProcessRepository,
)


class TestUserProcessRepository:
    """Tests for UserProcessRepository"""

    def test_init(self, db_session):
        """Test UserProcessRepository initialization"""
        repo = UserProcessRepository(db_session)
        assert repo.session is db_session

    def test_get_users_for_process_success(self, db_session, sample_user_process):
        """Test get_users_for_process returns user IDs for valid process"""
        repo = UserProcessRepository(db_session)

        user_ids = repo.get_users_for_process(sample_user_process.process_id)

        assert user_ids is not None
        assert len(user_ids) == 1
        assert sample_user_process.user_id in user_ids

    def test_get_users_for_process_multiple_users(self, db_session, sample_process):
        """Test get_users_for_process returns multiple user IDs"""
        user1 = User(email="user1@example.com", institution_id=201)
        user2 = User(email="user2@example.com", institution_id=202)
        db_session.add_all([user1, user2])
        db_session.commit()

        user_process1 = UserProcess(user_id=user1.id, process_id=sample_process.id)
        user_process2 = UserProcess(user_id=user2.id, process_id=sample_process.id)
        db_session.add_all([user_process1, user_process2])
        db_session.commit()

        repo = UserProcessRepository(db_session)
        user_ids = repo.get_users_for_process(sample_process.id)

        assert user_ids is not None
        assert len(user_ids) == 2
        assert user1.id in user_ids
        assert user2.id in user_ids

    def test_get_users_for_process_no_users(self, db_session, sample_process):
        """Test get_users_for_process returns empty list when no users found"""
        repo = UserProcessRepository(db_session)

        user_ids = repo.get_users_for_process(sample_process.id)

        assert user_ids == []

    def test_get_users_for_process_non_existent_process(self, db_session):
        """Test get_users_for_process returns empty list for non-existent process"""
        repo = UserProcessRepository(db_session)

        user_ids = repo.get_users_for_process(99999)

        assert user_ids == []

    @patch("alma_item_checks_notification_service.repos.user_process_repo.logging")
    def test_get_users_for_process_no_result_found(self, mock_logging, db_session):
        """Test get_users_for_process handles NoResultFound exception"""
        repo = UserProcessRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = NoResultFound()

            user_ids = repo.get_users_for_process(1)

            assert user_ids is None
            mock_logging.error.assert_called_with(
                "UserProcessRepository.get_users_for_process: NoResultFound"
            )

    @patch("alma_item_checks_notification_service.repos.user_process_repo.logging")
    def test_get_users_for_process_sqlalchemy_error(self, mock_logging, db_session):
        """Test get_users_for_process handles SQLAlchemyError"""
        repo = UserProcessRepository(db_session)
        error_msg = "Database connection error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError(error_msg)

            user_ids = repo.get_users_for_process(1)

            assert user_ids is None
            mock_logging.error.assert_called_with(
                f"UserProcessRepository.get_users_for_process: SQLAlchemyError: {error_msg}"
            )

    @patch("alma_item_checks_notification_service.repos.user_process_repo.logging")
    def test_get_users_for_process_general_exception(self, mock_logging, db_session):
        """Test get_users_for_process handles general exceptions"""
        repo = UserProcessRepository(db_session)
        error_msg = "Unexpected error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = Exception(error_msg)

            user_ids = repo.get_users_for_process(1)

            assert user_ids is None
            mock_logging.error.assert_called_with(
                f"UserProcessRepository.get_users_for_process: Exception: {error_msg}"
            )

    def test_get_users_for_process_returns_integers(
        self, db_session, sample_user_process
    ):
        """Test get_users_for_process returns integer user IDs"""
        repo = UserProcessRepository(db_session)

        user_ids = repo.get_users_for_process(sample_user_process.process_id)

        assert user_ids is not None
        assert len(user_ids) == 1
        assert isinstance(user_ids[0], int)
        assert user_ids[0] == sample_user_process.user_id

    def test_get_users_for_process_different_processes(self, db_session):
        """Test get_users_for_process distinguishes between different processes"""
        user1 = User(email="user1@example.com", institution_id=301)
        user2 = User(email="user2@example.com", institution_id=302)
        process1 = Process(
            name="process1",
            email_subject="Subject 1",
            email_body="Body 1",
            container="container1",
        )
        process2 = Process(
            name="process2",
            email_subject="Subject 2",
            email_body="Body 2",
            container="container2",
        )
        db_session.add_all([user1, user2, process1, process2])
        db_session.commit()

        user_process1 = UserProcess(user_id=user1.id, process_id=process1.id)
        user_process2 = UserProcess(user_id=user2.id, process_id=process2.id)
        db_session.add_all([user_process1, user_process2])
        db_session.commit()

        repo = UserProcessRepository(db_session)

        user_ids_process1 = repo.get_users_for_process(process1.id)
        user_ids_process2 = repo.get_users_for_process(process2.id)

        assert user_ids_process1 == [user1.id]
        assert user_ids_process2 == [user2.id]
        assert user_ids_process1 != user_ids_process2
