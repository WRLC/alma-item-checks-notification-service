"""Tests for database module"""

import pytest
from unittest.mock import patch, Mock

from alma_item_checks_notification_service import database


class TestDatabase:
    """Tests for database module"""

    def test_get_engine_missing_connection_string(self):
        """Test get_engine raises error when connection string missing"""
        # Reset global variables
        database._db_engine = None
        database._session_maker = None

        with patch(
            "alma_item_checks_notification_service.database.SQLALCHEMY_CONNECTION_STRING",
            None,
        ):
            with pytest.raises(
                ValueError,
                match="SQLALCHEMY_CONNECTION_STRING environment variable not set",
            ):
                database.get_engine()

    def test_get_engine_success(self):
        """Test get_engine creates engine successfully"""
        # Reset global variables
        database._db_engine = None
        database._session_maker = None

        with patch(
            "alma_item_checks_notification_service.database.SQLALCHEMY_CONNECTION_STRING",
            "sqlite:///:memory:",
        ):
            with patch(
                "alma_item_checks_notification_service.database.create_engine"
            ) as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine

                engine = database.get_engine()

                assert engine is mock_engine
                assert database._db_engine is mock_engine
                mock_create_engine.assert_called_once_with(
                    "sqlite:///:memory:", echo=True, pool_pre_ping=True
                )

    def test_get_engine_reuses_existing(self):
        """Test get_engine reuses existing engine"""
        # Set up existing engine
        mock_engine = Mock()
        database._db_engine = mock_engine

        engine = database.get_engine()

        assert engine is mock_engine

    def test_get_session_maker_success(self):
        """Test get_session_maker creates session maker"""
        # Reset global variables
        database._db_engine = None
        database._session_maker = None

        with patch(
            "alma_item_checks_notification_service.database.SQLALCHEMY_CONNECTION_STRING",
            "sqlite:///:memory:",
        ):
            with patch(
                "alma_item_checks_notification_service.database.create_engine"
            ) as mock_create_engine:
                with patch(
                    "alma_item_checks_notification_service.database.sessionmaker"
                ) as mock_sessionmaker:
                    mock_engine = Mock()
                    mock_session_maker = Mock()
                    mock_create_engine.return_value = mock_engine
                    mock_sessionmaker.return_value = mock_session_maker

                    session_maker = database.get_session_maker()

                    assert session_maker is mock_session_maker
                    assert database._session_maker is mock_session_maker
                    mock_sessionmaker.assert_called_once_with(bind=mock_engine)

    def test_get_session_maker_reuses_existing(self):
        """Test get_session_maker reuses existing session maker"""
        mock_session_maker = Mock()
        database._session_maker = mock_session_maker

        session_maker = database.get_session_maker()

        assert session_maker is mock_session_maker

    def test_session_maker_function(self):
        """Test SessionMaker function"""
        mock_session_maker = Mock()
        mock_session = Mock()
        mock_session_maker.return_value = mock_session
        database._session_maker = mock_session_maker

        session = database.SessionMaker()

        assert session is mock_session
        mock_session_maker.assert_called_once()
