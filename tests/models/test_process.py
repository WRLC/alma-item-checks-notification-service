"""Tests for Process model"""

import pytest

from alma_item_checks_notification_service.models.process import Process


class TestProcess:
    """Tests for Process model"""

    def test_process_model_creation(self, db_session):
        """Test Process model creation"""
        process = Process(
            name="test_process",
            email_subject="Test Subject",
            email_body="Test Body",
            email_addendum="Test Addendum",
            container="test_container",
        )
        db_session.add(process)
        db_session.commit()

        assert process.id is not None
        assert process.name == "test_process"
        assert process.email_subject == "Test Subject"
        assert process.email_body == "Test Body"
        assert process.email_addendum == "Test Addendum"
        assert process.container == "test_container"

    def test_process_model_table_name(self):
        """Test Process model table name"""
        assert Process.__tablename__ == "process"

    def test_process_model_attributes(self):
        """Test Process model has expected attributes"""
        process = Process()
        assert hasattr(process, "id")
        assert hasattr(process, "name")
        assert hasattr(process, "email_subject")
        assert hasattr(process, "email_body")
        assert hasattr(process, "email_addendum")
        assert hasattr(process, "container")

    def test_process_with_null_addendum(self, db_session):
        """Test Process can have null email_addendum"""
        process = Process(
            name="no_addendum_process",
            email_subject="Subject",
            email_body="Body",
            email_addendum=None,
            container="container",
        )
        db_session.add(process)
        db_session.commit()

        assert process.id is not None
        assert process.email_addendum is None

    def test_process_required_fields(self, db_session):
        """Test Process requires certain fields"""
        # Test missing name
        process = Process(
            email_subject="Subject", email_body="Body", container="container"
        )
        db_session.add(process)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

        db_session.rollback()

        # Test missing email_subject
        process = Process(name="test", email_body="Body", container="container")
        db_session.add(process)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
