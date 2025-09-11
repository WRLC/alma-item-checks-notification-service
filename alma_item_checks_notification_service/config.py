"""Configuration file for alma_item_checks_processor_service."""

import os

STORAGE_CONNECTION_SETTING_NAME = "AzureWebJobsStorage"
STORAGE_CONNECTION_STRING = os.getenv(STORAGE_CONNECTION_SETTING_NAME)

SQLALCHEMY_CONNECTION_STRING = os.getenv("SQLALCHEMY_CONNECTION_STRING")

NOTIFICATION_QUEUE = os.getenv(
    "NOTIFICATION_QUEUE", "notification-queue"
)  # Triggers function

ACS_STORAGE_CONNECTION_STRING: str | None = os.getenv("ACS_STORAGE_CONNECTION_STRING")
ACS_SENDER_QUEUE_NAME: str = os.getenv("ACS_SENDER_QUEUE_NAME", "")
ACS_SENDER_CONTAINER_NAME: str = os.getenv("ACS_SENDER_CONTAINER_NAME", "")

API_CLIENT_TIMEOUT = int(os.getenv("API_CLIENT_TIMEOUT", 90))
