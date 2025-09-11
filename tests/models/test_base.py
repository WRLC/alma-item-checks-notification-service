"""Tests for base model"""
import pytest

from alma_item_checks_notification_service.models.base import Base


class TestBase:
    """Tests for Base model"""
    
    def test_base_class_exists(self):
        """Test Base class exists and is a DeclarativeBase"""
        assert Base is not None
        assert hasattr(Base, 'registry')
        
    def test_base_is_declarative_base(self):
        """Test Base inherits from DeclarativeBase"""
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(Base, DeclarativeBase)