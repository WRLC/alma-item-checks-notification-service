"""Tests for UserProcessService"""
import pytest
from unittest.mock import Mock, patch

from alma_item_checks_notification_service.services.user_process_service import UserProcessService
from alma_item_checks_notification_service.repos.user_process_repo import UserProcessRepository
from alma_item_checks_notification_service.services.process_service import ProcessService
from alma_item_checks_notification_service.services.user_service import UserService


class TestUserProcessService:
    """Tests for UserProcessService"""
    
    def test_init(self, db_session):
        """Test UserProcessService initialization"""
        service = UserProcessService(db_session)
        assert isinstance(service.process_service, ProcessService)
        assert isinstance(service.user_process_repo, UserProcessRepository)
        assert isinstance(service.user_service, UserService)
        assert service.user_process_repo.session is db_session
    
    def test_get_user_emails_for_process_success(self, db_session, sample_user_process, sample_user, sample_process):
        """Test get_user_emails_for_process returns emails for valid process"""
        service = UserProcessService(db_session)
        
        emails = service.get_user_emails_for_process(sample_process.id, sample_user.institution_id)
        
        assert emails is not None
        assert len(emails) == 1
        assert sample_user.email in emails
    
    def test_get_user_emails_for_process_no_users(self, db_session, sample_process):
        """Test get_user_emails_for_process returns empty list when no users found"""
        service = UserProcessService(db_session)
        
        emails = service.get_user_emails_for_process(sample_process.id, 123)
        
        assert emails == []
    
    def test_get_user_emails_for_process_repo_returns_none(self, db_session):
        """Test get_user_emails_for_process returns empty list when repo returns None"""
        service = UserProcessService(db_session)
        
        with patch.object(service.user_process_repo, 'get_users_for_process', return_value=None):
            emails = service.get_user_emails_for_process(1, 123)
            
            assert emails == []
    
    def test_get_user_emails_for_process_multiple_users(self, db_session, sample_process):
        """Test get_user_emails_for_process returns multiple emails"""
        from alma_item_checks_notification_service.models.user import User
        from alma_item_checks_notification_service.models.user_process import UserProcess
        
        user1 = User(email="user1@example.com", institution_id=300)
        user2 = User(email="user2@example.com", institution_id=301) 
        db_session.add_all([user1, user2])
        db_session.commit()
        
        user_process1 = UserProcess(user_id=user1.id, process_id=sample_process.id)
        user_process2 = UserProcess(user_id=user2.id, process_id=sample_process.id)
        db_session.add_all([user_process1, user_process2])
        db_session.commit()
        
        service = UserProcessService(db_session)
        
        emails1 = service.get_user_emails_for_process(sample_process.id, user1.institution_id)
        emails2 = service.get_user_emails_for_process(sample_process.id, user2.institution_id)
        
        assert len(emails1) == 1
        assert len(emails2) == 1
        assert "user1@example.com" in emails1
        assert "user2@example.com" in emails2
    
    def test_get_user_emails_for_process_user_email_not_found(self, db_session, sample_process):
        """Test get_user_emails_for_process skips users with no email"""
        service = UserProcessService(db_session)
        
        # Mock user_process_repo to return user IDs
        with patch.object(service.user_process_repo, 'get_users_for_process', return_value=[1, 2, 3]):
            # Mock user_service to return emails for some users but not others
            with patch.object(service.user_service, 'get_user_email', side_effect=[
                "user1@example.com", None, "user3@example.com"
            ]) as mock_get_email:
                emails = service.get_user_emails_for_process(sample_process.id, 123)
                
                # Should call get_user_email for each user ID
                assert mock_get_email.call_count == 3
                mock_get_email.assert_any_call(1, 123)
                mock_get_email.assert_any_call(2, 123)
                mock_get_email.assert_any_call(3, 123)
                
                # Should only return valid emails
                assert emails == ["user1@example.com", "user3@example.com"]
    
    def test_get_user_emails_for_process_calls_dependencies(self, db_session):
        """Test get_user_emails_for_process calls correct dependency methods"""
        service = UserProcessService(db_session)
        
        with patch.object(service.user_process_repo, 'get_users_for_process', return_value=[1, 2]) as mock_get_users:
            with patch.object(service.user_service, 'get_user_email', return_value="test@example.com") as mock_get_email:
                emails = service.get_user_emails_for_process(123, 456)
                
                mock_get_users.assert_called_once_with(123)
                assert mock_get_email.call_count == 2
                mock_get_email.assert_any_call(1, 456)
                mock_get_email.assert_any_call(2, 456)
                assert emails == ["test@example.com", "test@example.com"]
    
    def test_get_user_emails_for_process_handles_exceptions(self, db_session):
        """Test get_user_emails_for_process handles exceptions from dependencies"""
        service = UserProcessService(db_session)
        
        with patch.object(service.user_process_repo, 'get_users_for_process', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                service.get_user_emails_for_process(1, 123)
        
        with patch.object(service.user_process_repo, 'get_users_for_process', return_value=[1]):
            with patch.object(service.user_service, 'get_user_email', side_effect=Exception("Email error")):
                with pytest.raises(Exception, match="Email error"):
                    service.get_user_emails_for_process(1, 123)
    
    def test_get_user_emails_for_process_empty_user_list(self, db_session):
        """Test get_user_emails_for_process with empty user list"""
        service = UserProcessService(db_session)
        
        with patch.object(service.user_process_repo, 'get_users_for_process', return_value=[]):
            emails = service.get_user_emails_for_process(1, 123)
            
            assert emails == []
    
    def test_get_user_emails_for_process_filters_empty_emails(self, db_session):
        """Test get_user_emails_for_process filters out None and empty emails"""
        service = UserProcessService(db_session)
        
        with patch.object(service.user_process_repo, 'get_users_for_process', return_value=[1, 2, 3, 4]):
            with patch.object(service.user_service, 'get_user_email', side_effect=[
                "valid@example.com", None, "", "another@example.com"
            ]):
                emails = service.get_user_emails_for_process(1, 123)
                
                # Should only include non-None, non-empty emails
                assert emails == ["valid@example.com", "another@example.com"]