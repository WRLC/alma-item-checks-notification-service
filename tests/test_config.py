"""Tests for configuration module"""
import os
from unittest.mock import patch

import pytest

import alma_item_checks_notification_service.config as config


class TestConfig:
    """Tests for config module"""
    
    def test_storage_connection_setting_name(self):
        """Test STORAGE_CONNECTION_SETTING_NAME constant"""
        assert config.STORAGE_CONNECTION_SETTING_NAME == "AzureWebJobsStorage"
    
    def test_storage_connection_string_from_env(self, monkeypatch):
        """Test STORAGE_CONNECTION_STRING reads from environment"""
        test_connection = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;"
        monkeypatch.setenv("AzureWebJobsStorage", test_connection)
        
        # Reload config module to pick up new env var
        import importlib
        importlib.reload(config)
        
        assert config.STORAGE_CONNECTION_STRING == test_connection
    
    def test_sqlalchemy_connection_string_from_env(self, monkeypatch):
        """Test SQLALCHEMY_CONNECTION_STRING reads from environment"""
        test_connection = "mysql://user:pass@host/db"
        monkeypatch.setenv("SQLALCHEMY_CONNECTION_STRING", test_connection)
        
        import importlib
        importlib.reload(config)
        
        assert config.SQLALCHEMY_CONNECTION_STRING == test_connection
    
    def test_notification_queue_default(self, monkeypatch):
        """Test NOTIFICATION_QUEUE has default value"""
        monkeypatch.delenv("NOTIFICATION_QUEUE", raising=False)
        
        import importlib
        importlib.reload(config)
        
        assert config.NOTIFICATION_QUEUE == "notification-queue"
    
    def test_notification_queue_from_env(self, monkeypatch):
        """Test NOTIFICATION_QUEUE reads from environment"""
        test_queue = "custom-queue"
        monkeypatch.setenv("NOTIFICATION_QUEUE", test_queue)
        
        import importlib
        importlib.reload(config)
        
        assert config.NOTIFICATION_QUEUE == test_queue
    
    def test_acs_storage_connection_string_from_env(self, monkeypatch):
        """Test ACS_STORAGE_CONNECTION_STRING reads from environment"""
        test_connection = "DefaultEndpointsProtocol=https;AccountName=acs;"
        monkeypatch.setenv("ACS_STORAGE_CONNECTION_STRING", test_connection)
        
        import importlib
        importlib.reload(config)
        
        assert config.ACS_STORAGE_CONNECTION_STRING == test_connection
    
    def test_acs_storage_connection_string_none(self, monkeypatch):
        """Test ACS_STORAGE_CONNECTION_STRING can be None"""
        monkeypatch.delenv("ACS_STORAGE_CONNECTION_STRING", raising=False)
        
        import importlib
        importlib.reload(config)
        
        assert config.ACS_STORAGE_CONNECTION_STRING is None
    
    def test_acs_sender_queue_name_default(self, monkeypatch):
        """Test ACS_SENDER_QUEUE_NAME has default empty string"""
        monkeypatch.delenv("ACS_SENDER_QUEUE_NAME", raising=False)
        
        import importlib
        importlib.reload(config)
        
        assert config.ACS_SENDER_QUEUE_NAME == ""
    
    def test_acs_sender_queue_name_from_env(self, monkeypatch):
        """Test ACS_SENDER_QUEUE_NAME reads from environment"""
        test_queue = "acs-sender-queue"
        monkeypatch.setenv("ACS_SENDER_QUEUE_NAME", test_queue)
        
        import importlib
        importlib.reload(config)
        
        assert config.ACS_SENDER_QUEUE_NAME == test_queue
    
    def test_acs_sender_container_name_default(self, monkeypatch):
        """Test ACS_SENDER_CONTAINER_NAME has default empty string"""
        monkeypatch.delenv("ACS_SENDER_CONTAINER_NAME", raising=False)
        
        import importlib
        importlib.reload(config)
        
        assert config.ACS_SENDER_CONTAINER_NAME == ""
    
    def test_acs_sender_container_name_from_env(self, monkeypatch):
        """Test ACS_SENDER_CONTAINER_NAME reads from environment"""
        test_container = "acs-sender-container"
        monkeypatch.setenv("ACS_SENDER_CONTAINER_NAME", test_container)
        
        import importlib
        importlib.reload(config)
        
        assert config.ACS_SENDER_CONTAINER_NAME == test_container
    
    def test_api_client_timeout_default(self, monkeypatch):
        """Test API_CLIENT_TIMEOUT has default value"""
        monkeypatch.delenv("API_CLIENT_TIMEOUT", raising=False)
        
        import importlib
        importlib.reload(config)
        
        assert config.API_CLIENT_TIMEOUT == 90
    
    def test_api_client_timeout_from_env(self, monkeypatch):
        """Test API_CLIENT_TIMEOUT reads from environment"""
        monkeypatch.setenv("API_CLIENT_TIMEOUT", "120")
        
        import importlib
        importlib.reload(config)
        
        assert config.API_CLIENT_TIMEOUT == 120
    
    def test_api_client_timeout_type_conversion(self, monkeypatch):
        """Test API_CLIENT_TIMEOUT converts to int"""
        monkeypatch.setenv("API_CLIENT_TIMEOUT", "30")
        
        import importlib
        importlib.reload(config)
        
        assert isinstance(config.API_CLIENT_TIMEOUT, int)
        assert config.API_CLIENT_TIMEOUT == 30