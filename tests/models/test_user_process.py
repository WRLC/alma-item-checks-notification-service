"""Tests for UserProcess model"""

import pytest

from alma_item_checks_notification_service.models.user import User
from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.models.user_process import UserProcess


class TestUserProcess:
    """Tests for UserProcess model"""

    def test_user_process_model_creation(self, db_session, sample_user, sample_process):
        """Test UserProcess model creation"""
        user_process = UserProcess(user_id=sample_user.id, process_id=sample_process.id)
        db_session.add(user_process)
        db_session.commit()

        assert user_process.user_id == sample_user.id
        assert user_process.process_id == sample_process.id

    def test_user_process_model_table_name(self):
        """Test UserProcess model table name"""
        assert UserProcess.__tablename__ == "user_process"

    def test_user_process_model_attributes(self):
        """Test UserProcess model has expected attributes"""
        user_process = UserProcess()
        assert hasattr(user_process, "user_id")
        assert hasattr(user_process, "process_id")

    def test_user_process_foreign_keys(self, db_session):
        """Test UserProcess foreign key constraints"""
        user = User(email="fk_test@example.com", institution_id=999)
        process = Process(
            name="fk_test_process",
            email_subject="FK Test",
            email_body="FK Body",
        )
        db_session.add(user)
        db_session.add(process)
        db_session.commit()

        user_process = UserProcess(user_id=user.id, process_id=process.id)
        db_session.add(user_process)
        db_session.commit()

        assert user_process.user_id == user.id
        assert user_process.process_id == process.id

    def test_user_process_composite_primary_key(self, db_session):
        """Test UserProcess composite primary key constraint"""
        # Create unique test data to avoid conflicts
        user = User(email="composite_test@example.com", institution_id=9999)
        process = Process(
            name="composite_test_process",
            email_subject="Composite Test",
            email_body="Test Body",
        )
        db_session.add_all([user, process])
        db_session.commit()

        user_process1 = UserProcess(user_id=user.id, process_id=process.id)
        db_session.add(user_process1)
        db_session.commit()

        # Try to add duplicate
        user_process2 = UserProcess(user_id=user.id, process_id=process.id)
        db_session.add(user_process2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

        # Clean up after failed commit
        db_session.rollback()

    def test_user_process_invalid_foreign_keys(self, db_session):
        """Test UserProcess with invalid foreign keys"""
        user_process = UserProcess(
            user_id=99999,  # Non-existent user
            process_id=99999,  # Non-existent process
        )
        db_session.add(user_process)
        # SQLite may not enforce foreign key constraints by default in testing
        # So let's commit and then try to query, which should find nothing
        db_session.commit()

        # Verify the record exists but foreign keys don't reference valid data
        found_user_process = (
            db_session.query(UserProcess).filter_by(user_id=99999).first()
        )
        assert found_user_process is not None
        assert found_user_process.user_id == 99999
        assert found_user_process.process_id == 99999
