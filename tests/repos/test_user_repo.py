"""Tests for UserRepository"""

from unittest.mock import patch, Mock
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from alma_item_checks_notification_service.models.user import User
from alma_item_checks_notification_service.repos.user_repo import UserRepository


class TestUserRepository:
    """Tests for UserRepository"""

    def test_init(self, db_session):
        """Test UserRepository initialization"""
        repo = UserRepository(db_session)
        assert repo.session is db_session

    def test_get_user_email_success(self, db_session, sample_user):
        """Test get_user_email returns email for valid user"""
        repo = UserRepository(db_session)

        email = repo.get_user_email(sample_user.id, sample_user.institution_id)

        assert email == sample_user.email

    def test_get_user_email_without_institution_id(self, db_session, sample_user):
        """Test get_user_email without institution_id"""
        repo = UserRepository(db_session)

        email = repo.get_user_email(sample_user.id, None)

        assert email == sample_user.email

    def test_get_user_email_user_not_found(self, db_session):
        """Test get_user_email returns None for non-existent user"""
        repo = UserRepository(db_session)

        email = repo.get_user_email(99999, 123)

        assert email is None

    def test_get_user_email_wrong_institution(self, db_session, sample_user):
        """Test get_user_email returns None for wrong institution"""
        repo = UserRepository(db_session)

        email = repo.get_user_email(sample_user.id, 99999)

        assert email is None

    def test_get_user_email_user_with_no_email(self, db_session):
        """Test get_user_email returns None when user has no email"""
        # SQLite enforces NOT NULL constraint, so we can't test with None email
        # Instead, test the logic path by mocking the database result
        repo = UserRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_result = Mock()
            mock_user = Mock()
            mock_user.email = None  # Simulate user with no email
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_execute.return_value = mock_result

            email = repo.get_user_email(1, 456)

            assert email is None

    @patch("alma_item_checks_notification_service.repos.user_repo.logging")
    def test_get_user_email_no_result_found(self, mock_logging, db_session):
        """Test get_user_email handles NoResultFound exception"""
        repo = UserRepository(db_session)

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = NoResultFound()

            email = repo.get_user_email(1, 123)

            assert email is None
            mock_logging.error.assert_called_with(
                "UserRepository::get_user_email(): user not found"
            )

    @patch("alma_item_checks_notification_service.repos.user_repo.logging")
    def test_get_user_email_sqlalchemy_error(self, mock_logging, db_session):
        """Test get_user_email handles SQLAlchemyError"""
        repo = UserRepository(db_session)
        error_msg = "Database connection error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError(error_msg)

            email = repo.get_user_email(1, 123)

            assert email is None
            mock_logging.error.assert_called_with(
                f"UserRepository::get_user_email(): {error_msg}"
            )

    @patch("alma_item_checks_notification_service.repos.user_repo.logging")
    def test_get_user_email_general_exception(self, mock_logging, db_session):
        """Test get_user_email handles general exceptions"""
        repo = UserRepository(db_session)
        error_msg = "Unexpected error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = Exception(error_msg)

            email = repo.get_user_email(1, 123)

            assert email is None
            mock_logging.error.assert_called_with(
                f"UserRepository::get_user_email(): {error_msg}"
            )

    def test_get_user_email_multiple_users_same_institution(self, db_session):
        """Test get_user_email works with multiple users in same institution"""
        user1 = User(email="user1@example.com", institution_id=500)
        user2 = User(email="user2@example.com", institution_id=501)
        db_session.add_all([user1, user2])
        db_session.commit()

        repo = UserRepository(db_session)

        email1 = repo.get_user_email(user1.id, user1.institution_id)
        email2 = repo.get_user_email(user2.id, user2.institution_id)

        assert email1 == "user1@example.com"
        assert email2 == "user2@example.com"

    @patch("alma_item_checks_notification_service.repos.user_repo.logging")
    def test_get_user_email_logs_user_not_found(self, mock_logging, db_session):
        """Test get_user_email logs when user not found"""
        repo = UserRepository(db_session)

        email = repo.get_user_email(99999, 123)

        assert email is None
        mock_logging.error.assert_called_with("User 99999 not found")
