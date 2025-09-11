"""Tests for ProcessRepository"""

from unittest.mock import patch
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.repos.process_repo import ProcessRepository


class TestProcessRepository:
    """Tests for ProcessRepository"""

    def test_init(self, db_session):
        """Test ProcessRepository initialization"""
        repo = ProcessRepository(db_session)
        assert repo.session is db_session

    def test_get_process_by_name_success(self, db_session, sample_process):
        """Test get_process_by_name returns process for valid name"""
        repo = ProcessRepository(db_session)

        process = repo.get_process_by_name(sample_process.name)

        assert process is not None
        assert process.id == sample_process.id
        assert process.name == sample_process.name
        assert process.email_subject == sample_process.email_subject

    def test_get_process_by_name_not_found(self, db_session):
        """Test get_process_by_name returns None for non-existent process"""
        repo = ProcessRepository(db_session)

        process = repo.get_process_by_name("non_existent_process")

        assert process is None

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_by_name_logs_not_found(self, mock_logging, db_session):
        """Test get_process_by_name logs when process not found"""
        repo = ProcessRepository(db_session)
        process_name = "missing_process"

        process = repo.get_process_by_name(process_name)

        assert process is None
        mock_logging.error.assert_called_with(
            f"ProcessRepository::get_process_by_name: {process_name} not found"
        )

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_by_name_no_result_found(self, mock_logging, db_session):
        """Test get_process_by_name handles NoResultFound exception"""
        repo = ProcessRepository(db_session)
        process_name = "test_process"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = NoResultFound()

            process = repo.get_process_by_name(process_name)

            assert process is None
            mock_logging.error.assert_called_with(
                f"ProcessRepository.get_process_id_by_name: No process found with name '{process_name}'"
            )

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_by_name_sqlalchemy_error(self, mock_logging, db_session):
        """Test get_process_by_name handles SQLAlchemyError"""
        repo = ProcessRepository(db_session)
        error_msg = "Database error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError(error_msg)

            process = repo.get_process_by_name("test_process")

            assert process is None
            mock_logging.error.assert_called_with(
                f"ProcessRepository.get_process_id_by_name: SQLAlchemyError: {error_msg}"
            )

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_by_name_general_exception(self, mock_logging, db_session):
        """Test get_process_by_name handles general exceptions"""
        repo = ProcessRepository(db_session)
        error_msg = "Unexpected error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = Exception(error_msg)

            process = repo.get_process_by_name("test_process")

            assert process is None
            mock_logging.error.assert_called_with(
                f"ProcessRepository.get_process_id_by_name: Exception: {error_msg}"
            )

    def test_get_process_id_by_name_success(self, db_session, sample_process):
        """Test get_process_id_by_name returns process id for valid name"""
        repo = ProcessRepository(db_session)

        process_id = repo.get_process_id_by_name(sample_process.name)

        assert process_id == sample_process.id

    def test_get_process_id_by_name_not_found(self, db_session):
        """Test get_process_id_by_name returns None for non-existent process"""
        repo = ProcessRepository(db_session)

        process_id = repo.get_process_id_by_name("non_existent_process")

        assert process_id is None

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_id_by_name_logs_not_found(self, mock_logging, db_session):
        """Test get_process_id_by_name logs when process not found"""
        repo = ProcessRepository(db_session)
        process_name = "missing_process"

        process_id = repo.get_process_id_by_name(process_name)

        assert process_id is None
        mock_logging.error.assert_called_with(
            f"ProcessRepository.get_process_id_by_name: Process '{process_name}' not found"
        )

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_id_by_name_no_result_found(self, mock_logging, db_session):
        """Test get_process_id_by_name handles NoResultFound exception"""
        repo = ProcessRepository(db_session)
        process_name = "test_process"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = NoResultFound()

            process_id = repo.get_process_id_by_name(process_name)

            assert process_id is None
            mock_logging.error.assert_called_with(
                f"ProcessRepository.get_process_id_by_name: No process found with name '{process_name}'"
            )

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_id_by_name_sqlalchemy_error(self, mock_logging, db_session):
        """Test get_process_id_by_name handles SQLAlchemyError"""
        repo = ProcessRepository(db_session)
        error_msg = "Database error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError(error_msg)

            process_id = repo.get_process_id_by_name("test_process")

            assert process_id is None
            mock_logging.error.assert_called_with(
                f"ProcessRepository.get_process_id_by_name: SQLAlchemyError: {error_msg}"
            )

    @patch("alma_item_checks_notification_service.repos.process_repo.logging")
    def test_get_process_id_by_name_general_exception(self, mock_logging, db_session):
        """Test get_process_id_by_name handles general exceptions"""
        repo = ProcessRepository(db_session)
        error_msg = "Unexpected error"

        with patch.object(db_session, "execute") as mock_execute:
            mock_execute.side_effect = Exception(error_msg)

            process_id = repo.get_process_id_by_name("test_process")

            assert process_id is None
            mock_logging.error.assert_called_with(
                f"ProcessRepository.get_process_id_by_name: Exception: {error_msg}"
            )

    def test_multiple_processes(self, db_session):
        """Test repository works with multiple processes"""
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
        db_session.add_all([process1, process2])
        db_session.commit()

        repo = ProcessRepository(db_session)

        found_process1 = repo.get_process_by_name("process1")
        found_process2 = repo.get_process_by_name("process2")

        assert found_process1.name == "process1"
        assert found_process2.name == "process2"
        assert found_process1.id != found_process2.id
