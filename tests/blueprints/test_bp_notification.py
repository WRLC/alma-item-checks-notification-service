"""Tests for bp_notification blueprint"""
import json
from unittest.mock import Mock, patch, MagicMock
import pytest
import azure.functions as func

from alma_item_checks_notification_service.blueprints.bp_notification import send_notification
from alma_item_checks_notification_service.models.user import User
from alma_item_checks_notification_service.models.process import Process
from alma_item_checks_notification_service.models.user_process import UserProcess


class TestBpNotification:
    """Tests for bp_notification blueprint"""
    
    def test_send_notification_function_exists(self):
        """Test send_notification function exists and is callable"""
        assert callable(send_notification)
    
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker')
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService')
    def test_send_notification_success(self, mock_notification_service_class, mock_session_maker_class):
        """Test send_notification function processes message successfully"""
        # Create mock queue message
        mock_message = Mock(spec=func.QueueMessage)
        
        # Create mock session and session maker
        mock_session = Mock()
        mock_session_maker_class.return_value.__enter__.return_value = mock_session
        mock_session_maker_class.return_value.__exit__.return_value = None
        
        # Create mock notification service
        mock_notification_service = Mock()
        mock_notification_service_class.return_value = mock_notification_service
        
        # Call the function
        send_notification(mock_message)
        
        # Verify initialization and calls
        mock_notification_service_class.assert_called_once_with(mock_message)
        mock_notification_service.send_notification.assert_called_once_with(mock_session)
        mock_session_maker_class.assert_called_once()
    
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker')
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService')
    def test_send_notification_service_exception(self, mock_notification_service_class, mock_session_maker_class):
        """Test send_notification handles NotificationService exceptions"""
        # Create mock queue message
        mock_message = Mock(spec=func.QueueMessage)
        
        # Create mock session and session maker
        mock_session = Mock()
        mock_session_maker_class.return_value.__enter__.return_value = mock_session
        mock_session_maker_class.return_value.__exit__.return_value = None
        
        # Create mock notification service that raises exception
        mock_notification_service = Mock()
        mock_notification_service.send_notification.side_effect = Exception("Service error")
        mock_notification_service_class.return_value = mock_notification_service
        
        # Should propagate the exception
        with pytest.raises(Exception, match="Service error"):
            send_notification(mock_message)
        
        # Verify calls were made before exception
        mock_notification_service_class.assert_called_once_with(mock_message)
        mock_notification_service.send_notification.assert_called_once_with(mock_session)
    
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker')
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService')
    def test_send_notification_session_context_manager(self, mock_notification_service_class, mock_session_maker_class):
        """Test send_notification uses session as context manager properly"""
        # Create mock queue message
        mock_message = Mock(spec=func.QueueMessage)
        
        # Create mock session maker with context manager behavior
        mock_session_context = MagicMock()
        mock_session = Mock()
        mock_session_context.__enter__.return_value = mock_session
        mock_session_context.__exit__.return_value = None
        mock_session_maker_class.return_value = mock_session_context
        
        # Create mock notification service
        mock_notification_service = Mock()
        mock_notification_service_class.return_value = mock_notification_service
        
        # Call the function
        send_notification(mock_message)
        
        # Verify context manager usage
        mock_session_context.__enter__.assert_called_once()
        mock_session_context.__exit__.assert_called_once()
        mock_notification_service.send_notification.assert_called_once_with(mock_session)
    
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker')
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService')
    def test_send_notification_session_exception_handling(self, mock_notification_service_class, mock_session_maker_class):
        """Test send_notification handles session exceptions properly"""
        # Create mock queue message
        mock_message = Mock(spec=func.QueueMessage)
        
        # Create mock session maker that raises exception in context manager
        mock_session_context = MagicMock()
        mock_session_context.__enter__.side_effect = Exception("Session error")
        mock_session_maker_class.return_value = mock_session_context
        
        # Create mock notification service
        mock_notification_service = Mock()
        mock_notification_service_class.return_value = mock_notification_service
        
        # Should propagate the session exception
        with pytest.raises(Exception, match="Session error"):
            send_notification(mock_message)
        
        # NotificationService should be called (it's instantiated before session creation)
        # but send_notification should not be called due to session failure
        mock_notification_service_class.assert_called_once_with(mock_message)
        mock_notification_service.send_notification.assert_not_called()
    
    def test_send_notification_return_type(self):
        """Test send_notification returns None as expected for Azure Functions"""
        mock_message = Mock(spec=func.QueueMessage)
        
        with patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker'):
            with patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService'):
                result = send_notification(mock_message)
                
                assert result is None
    
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker')
    @patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService')
    def test_send_notification_parameter_types(self, mock_notification_service_class, mock_session_maker_class):
        """Test send_notification accepts correct parameter types"""
        # Test with proper QueueMessage mock
        mock_message = Mock(spec=func.QueueMessage)
        
        mock_session = Mock()
        mock_session_maker_class.return_value.__enter__.return_value = mock_session
        mock_session_maker_class.return_value.__exit__.return_value = None
        
        mock_notification_service = Mock()
        mock_notification_service_class.return_value = mock_notification_service
        
        # Should work without issues
        send_notification(mock_message)
        
        # Verify the message was passed correctly
        mock_notification_service_class.assert_called_once_with(mock_message)
    
    def test_blueprint_configuration(self):
        """Test blueprint is configured correctly"""
        # Test that the function exists and is callable
        assert callable(send_notification)
        # send_notification is a FunctionBuilder, not a regular function
        assert hasattr(send_notification, '_function')
        # Check the underlying function has the correct name
        if hasattr(send_notification, '_function') and send_notification._function:
            assert send_notification._function.get_function_name() == 'send_notification'

    def test_blueprint_function_integration(self, db_session):
        """Test blueprint function integration with database"""
        # Create mock message
        mock_message = Mock()
        mock_message.get_body.return_value.decode.return_value = json.dumps({
            "report_id": "integration_report",
            "institution_id": 100,
            "process_type": "integration_process"
        })
        
        # Test the blueprint function with mocked external services
        with patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker') as mock_session_maker:
            with patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService') as mock_notification_service:
                # Setup session context manager
                mock_context = MagicMock()
                mock_context.__enter__.return_value = db_session
                mock_context.__exit__.return_value = None
                mock_session_maker.return_value = mock_context
                
                # Setup notification service
                mock_service = Mock()
                mock_notification_service.return_value = mock_service
                
                # Call the function
                result = send_notification(mock_message)
                
                # Verify
                assert result is None
                mock_notification_service.assert_called_once_with(mock_message)
                mock_service.send_notification.assert_called_once_with(db_session)

    def test_service_layer_integration(self, db_session):
        """Test service layer integration"""
        from alma_item_checks_notification_service.services.user_service import UserService
        from alma_item_checks_notification_service.services.process_service import ProcessService
        from alma_item_checks_notification_service.services.user_process_service import UserProcessService
        
        # Setup test data
        user = User(email="service@example.com", institution_id=200)
        process = Process(
            name="service_process",
            email_subject="Service Test",
            email_body="Test body",
            container="service_container"
        )
        db_session.add_all([user, process])
        db_session.commit()
        
        user_process = UserProcess(user_id=user.id, process_id=process.id)
        db_session.add(user_process)
        db_session.commit()
        
        # Test service integration
        user_service = UserService(db_session)
        process_service = ProcessService(db_session)
        user_process_service = UserProcessService(db_session)
        
        # Test process service
        found_process = process_service.get_process_by_name("service_process")
        assert found_process is not None
        assert found_process.name == "service_process"
        
        # Test user service
        user_email = user_service.get_user_email(user.id, user.institution_id)
        assert user_email == "service@example.com"
        
        # Test user process service
        emails = user_process_service.get_user_emails_for_process(process.id, user.institution_id)
        assert emails == ["service@example.com"]

    def test_error_handling_integration(self, db_session):
        """Test error handling integration"""
        mock_message = Mock()
        mock_message.get_body.return_value.decode.return_value = json.dumps({
            "report_id": None,  # Missing field
            "institution_id": 123,
            "process_type": "nonexistent"
        })
        
        with patch('alma_item_checks_notification_service.blueprints.bp_notification.SessionMaker') as mock_session_maker:
            with patch('alma_item_checks_notification_service.blueprints.bp_notification.NotificationService') as mock_notification_service:
                mock_context = MagicMock()
                mock_context.__enter__.return_value = db_session
                mock_context.__exit__.return_value = None
                mock_session_maker.return_value = mock_context
                
                mock_service = Mock()
                mock_notification_service.return_value = mock_service
                
                # Should handle errors gracefully
                result = send_notification(mock_message)
                assert result is None
                mock_notification_service.assert_called_once_with(mock_message)
                mock_service.send_notification.assert_called_once_with(db_session)