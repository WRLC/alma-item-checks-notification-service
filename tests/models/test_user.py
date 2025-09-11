"""Tests for User model"""
import pytest

from alma_item_checks_notification_service.models.user import User


class TestUser:
    """Tests for User model"""
    
    def test_user_model_creation(self, db_session):
        """Test User model creation"""
        user = User(
            email="test@example.com",
            institution_id=123
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.institution_id == 123
    
    def test_user_model_table_name(self):
        """Test User model table name"""
        assert User.__tablename__ == "user"
    
    def test_user_model_attributes(self):
        """Test User model has expected attributes"""
        user = User()
        assert hasattr(user, 'id')
        assert hasattr(user, 'email')
        assert hasattr(user, 'institution_id')
        
    def test_user_email_unique_constraint(self, db_session):
        """Test user email unique constraint"""
        user1 = User(email="unique@example.com", institution_id=123)
        user2 = User(email="unique@example.com", institution_id=456)
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_institution_id_unique_constraint(self, db_session):
        """Test user institution_id unique constraint"""
        user1 = User(email="user1@example.com", institution_id=999)
        user2 = User(email="user2@example.com", institution_id=999)
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()