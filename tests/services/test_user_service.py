"""Tests for UserService"""
import pytest
from unittest.mock import Mock, patch

from alma_item_checks_notification_service.services.user_service import UserService
from alma_item_checks_notification_service.repos.user_repo import UserRepository


class TestUserService:
    """Tests for UserService"""
    
    def test_init(self, db_session):
        """Test UserService initialization"""
        service = UserService(db_session)
        assert isinstance(service.user_repo, UserRepository)
        assert service.user_repo.session is db_session
    
    def test_get_user_email_success(self, db_session, sample_user):
        """Test get_user_email returns email for valid user"""
        service = UserService(db_session)
        
        email = service.get_user_email(sample_user.id, sample_user.institution_id)
        
        assert email == sample_user.email
    
    def test_get_user_email_not_found(self, db_session):
        """Test get_user_email returns None when user not found"""
        service = UserService(db_session)
        
        email = service.get_user_email(99999, 123)
        
        assert email is None
    
    def test_get_user_email_calls_repo(self, db_session):
        """Test get_user_email calls repository method"""
        service = UserService(db_session)
        
        with patch.object(service.user_repo, 'get_user_email', return_value="test@example.com") as mock_get_email:
            result = service.get_user_email(1, 123)
            
            mock_get_email.assert_called_once_with(1, 123)
            assert result == "test@example.com"
    
    def test_get_user_email_forwards_none_institution_id(self, db_session):
        """Test get_user_email forwards None institution_id to repo"""
        service = UserService(db_session)
        
        with patch.object(service.user_repo, 'get_user_email', return_value="test@example.com") as mock_get_email:
            result = service.get_user_email(1, None)
            
            mock_get_email.assert_called_once_with(1, None)
            assert result == "test@example.com"
    
    def test_get_user_email_handles_repo_exception(self, db_session):
        """Test get_user_email handles repository exceptions"""
        service = UserService(db_session)
        
        with patch.object(service.user_repo, 'get_user_email', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                service.get_user_email(1, 123)
    
    def test_get_user_email_with_different_users(self, db_session):
        """Test get_user_email works with different user scenarios"""
        from alma_item_checks_notification_service.models.user import User
        
        user1 = User(email="user1@example.com", institution_id=100)
        user2 = User(email="user2@example.com", institution_id=200)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        service = UserService(db_session)
        
        email1 = service.get_user_email(user1.id, user1.institution_id)
        email2 = service.get_user_email(user2.id, user2.institution_id)
        
        assert email1 == "user1@example.com"
        assert email2 == "user2@example.com"
        
        # Test wrong institution
        wrong_email = service.get_user_email(user1.id, user2.institution_id)
        assert wrong_email is None