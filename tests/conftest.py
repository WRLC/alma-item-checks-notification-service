"""Pytest configuration and fixtures"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from alma_item_checks_notification_service.models.base import Base
from alma_item_checks_notification_service.models.user import User
from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.models.user_process import UserProcess


@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def sample_user(db_session):
    """Create sample user for testing"""
    user = User(id=1, email="test@example.com", institution_id=123)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def sample_process(db_session):
    """Create sample process for testing"""
    process = Process(
        id=1,
        name="test_process",
        email_subject="Test Subject",
        email_body="Test Body",
        email_addendum="Test Addendum",
        container="test_container",
    )
    db_session.add(process)
    db_session.commit()
    return process


@pytest.fixture(scope="function")
def sample_user_process(db_session, sample_user, sample_process):
    """Create sample user_process for testing"""
    user_process = UserProcess(user_id=sample_user.id, process_id=sample_process.id)
    db_session.add(user_process)
    db_session.commit()
    return user_process


@pytest.fixture
def mock_queue_message():
    """Mock Azure Functions QueueMessage"""
    message = Mock()
    message.get_body.return_value.decode.return_value = json.dumps(
        {
            "report_id": "test_report_123",
            "institution_id": 123,
            "process_type": "test_process",
        }
    )
    return message


@pytest.fixture
def mock_storage_service():
    """Mock StorageService"""
    mock = Mock()
    mock.download_blob_as_json.return_value = [
        {"column1": "value1", "column2": "value2"},
        {"column1": "value3", "column2": "value4"},
    ]
    return mock


@pytest.fixture
def sample_report_data():
    """Sample report data for testing"""
    return [
        {"Item ID": "123", "Title": "Test Book", "Status": "Available"},
        {"Item ID": "456", "Title": "Another Book", "Status": "Checked Out"},
    ]


@pytest.fixture
def temp_template_dir():
    """Create temporary template directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "templates"
        template_dir.mkdir()

        # Create test email template
        template_content = """
        <html>
        <body>
        <h1>{{ email_caption }}</h1>
        <p>{{ email_body }}</p>
        {{ data_table_html|safe }}
        <p>{{ body_addendum }}</p>
        </body>
        </html>
        """
        (template_dir / "email_template.html.j2").write_text(template_content.strip())

        yield template_dir


@pytest.fixture(autouse=True)
def setup_env_vars(monkeypatch):
    """Setup environment variables for testing"""
    monkeypatch.setenv("SQLALCHEMY_CONNECTION_STRING", "sqlite:///:memory:")
    monkeypatch.setenv(
        "AzureWebJobsStorage",
        "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=testkey;EndpointSuffix=core.windows.net",
    )
    monkeypatch.setenv("NOTIFICATION_QUEUE", "test-queue")
    monkeypatch.setenv(
        "ACS_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=acs;AccountKey=key;EndpointSuffix=core.windows.net",
    )
    monkeypatch.setenv("ACS_SENDER_QUEUE_NAME", "sender-queue")
    monkeypatch.setenv("ACS_SENDER_CONTAINER_NAME", "sender-container")
    monkeypatch.setenv("API_CLIENT_TIMEOUT", "90")


@pytest.fixture
def reset_global_variables():
    """Reset global database variables between tests"""
    import alma_item_checks_notification_service.database as db_module

    db_module._db_engine = None
    db_module._session_maker = None
    yield
    db_module._db_engine = None
    db_module._session_maker = None
