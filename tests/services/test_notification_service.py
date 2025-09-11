"""Tests for NotificationService"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from jinja2 import TemplateNotFound

from alma_item_checks_notification_service.services.notification_service import NotificationService


class TestNotificationService:
    """Tests for NotificationService"""

    def setup_method(self):
        """Setup for each test method"""
        self.mock_message = Mock()
        self.mock_message.get_body.return_value.decode.return_value = json.dumps({
            "report_id": "test_report",
            "institution_id": 123,
            "process_type": "test_process"
        })

    def test_init_success(self):
        """Test NotificationService initialization success"""
        # Test basic initialization success path by mocking the template directory check
        with patch('alma_item_checks_notification_service.services.notification_service.pathlib.Path'):
            with patch('alma_item_checks_notification_service.services.notification_service.Environment') as mock_env:
                with patch('alma_item_checks_notification_service.services.notification_service.StorageService') as mock_storage:
                    # Mock the template dir to exist
                    with patch('alma_item_checks_notification_service.services.notification_service.logging'):
                        mock_jinja_env = Mock()
                        mock_env.return_value = mock_jinja_env
                        
                        # Mock the path chain to succeed
                        with patch.object(Path, 'is_dir', return_value=True):
                            service = NotificationService(self.mock_message)
                            
                            assert service.msg is self.mock_message
                            mock_storage.assert_called_once()

    def test_init_template_directory_not_found(self):
        """Test initialization with missing template directory"""
        # Test the path where template directory doesn't exist
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            with patch.object(Path, 'is_dir', return_value=False):
                with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                    # The service catches the FileNotFoundError and logs it, setting jinja_env to None
                    service = NotificationService(self.mock_message)
                    assert service.jinja_env is None
                    mock_logging.error.assert_called()
                    mock_logging.exception.assert_called()

    def test_init_exception_handling(self):
        """Test initialization handles exceptions gracefully"""
        with patch('alma_item_checks_notification_service.services.notification_service.pathlib.Path', side_effect=Exception("Path error")):
            with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
                with patch('alma_item_checks_notification_service.services.notification_service.logging'):
                    service = NotificationService(self.mock_message)
                    assert service.jinja_env is None

    def test_send_notification_missing_fields(self):
        """Test send_notification with missing required fields"""
        mock_message = Mock()
        mock_message.get_body.return_value.decode.return_value = json.dumps({
            "report_id": None,
            "institution_id": 123,
            "process_type": "test"
        })
        
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                service = NotificationService(mock_message)
                service.jinja_env = None
                
                mock_session = Mock()
                service.send_notification(mock_session)
                
                mock_logging.error.assert_called_with(
                    "NotificationService.send_notification: message body missing required fields"
                )

    def test_send_notification_process_not_found(self):
        """Test send_notification with non-existent process"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            with patch('alma_item_checks_notification_service.services.notification_service.ProcessService') as mock_ps:
                with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                    service = NotificationService(self.mock_message)
                    service.jinja_env = None
                    
                    mock_process_service = Mock()
                    mock_process_service.get_process_by_name.return_value = None
                    mock_ps.return_value = mock_process_service
                    
                    mock_session = Mock()
                    service.send_notification(mock_session)
                    
                    mock_logging.error.assert_called_with(
                        "NotificationService.send_notification: process type test_process not found"
                    )

    def test_send_notification_success(self, sample_process, sample_user):
        """Test successful send_notification flow"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService') as mock_storage_class:
            # Setup storage service mocks
            mock_blob_storage = Mock()
            mock_acs_storage = Mock()
            mock_storage_class.side_effect = [mock_blob_storage, mock_acs_storage]
            
            mock_blob_storage.download_blob_as_json.return_value = [{"Item": "Test"}]
            
            # Mock config to have the container attribute
            with patch('alma_item_checks_notification_service.services.notification_service.config') as mock_config:
                setattr(mock_config, sample_process.container, sample_process.container)
                
                service = NotificationService(self.mock_message)
                
                # Mock successful jinja rendering
                mock_template = Mock()
                mock_template.render.return_value = "<html>test email</html>"
                mock_jinja_env = Mock()
                mock_jinja_env.get_template.return_value = mock_template
                service.jinja_env = mock_jinja_env
                
                # Mock the services
                with patch('alma_item_checks_notification_service.services.notification_service.ProcessService') as mock_ps:
                    with patch('alma_item_checks_notification_service.services.notification_service.UserProcessService') as mock_ups:
                        mock_process_service = Mock()
                        mock_process_service.get_process_by_name.return_value = sample_process
                        mock_ps.return_value = mock_process_service
                        
                        mock_user_process_service = Mock()
                        mock_user_process_service.get_user_emails_for_process.return_value = [sample_user.email]
                        mock_ups.return_value = mock_user_process_service
                        
                        # Mock pandas
                        with patch('alma_item_checks_notification_service.services.notification_service.pd') as mock_pd:
                            mock_df = Mock()
                            mock_df.empty = False
                            mock_df.to_html.return_value = "<table>test data</table>"
                            mock_df.style.set_caption.return_value = mock_df
                            mock_pd.read_json.return_value = mock_df
                            
                            mock_session = Mock()
                            service.send_notification(mock_session)
                            
                            # Verify the complete flow
                            mock_blob_storage.download_blob_as_json.assert_called_once()
                            mock_acs_storage.upload_blob_data.assert_called_once()
                            mock_acs_storage.send_queue_message.assert_called_once()

    def test_render_email_body_no_jinja_env(self):
        """Test render_email_body with no Jinja environment"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                service = NotificationService(self.mock_message)
                service.jinja_env = None
                
                result = service.render_email_body("template.html", Mock(), "table")
                
                assert result is None
                mock_logging.error.assert_called_with(
                    "NotificationService.render_email_body: Cannot render email, Jinja2 environment not available."
                )

    def test_render_email_body_template_not_found(self):
        """Test render_email_body with template not found"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            mock_jinja_env = Mock()
            mock_jinja_env.get_template.side_effect = TemplateNotFound("template.html")
            service.jinja_env = mock_jinja_env
            
            with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                result = service.render_email_body("template.html", Mock(), "table")
                
                assert result is None
                # Check that TemplateNotFound error was logged
                assert any("Template not found" in str(call) for call in mock_logging.error.call_args_list)

    def test_render_email_body_render_exception(self):
        """Test render_email_body with rendering exception"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            mock_template = Mock()
            mock_template.render.side_effect = Exception("Render error")
            mock_jinja_env = Mock()
            mock_jinja_env.get_template.return_value = mock_template
            service.jinja_env = mock_jinja_env
            
            with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                result = service.render_email_body("template.html", Mock(), "table")
                
                assert result is None
                assert any("Error rendering template" in str(call) for call in mock_logging.error.call_args_list)

    def test_render_email_body_success(self):
        """Test successful render_email_body"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            mock_template = Mock()
            mock_template.render.return_value = "<html>rendered content</html>"
            mock_jinja_env = Mock()
            mock_jinja_env.get_template.return_value = mock_template
            service.jinja_env = mock_jinja_env
            
            mock_process = Mock()
            mock_process.email_subject = "Test Subject"
            mock_process.email_body = "Test Body"
            mock_process.email_addendum = "Test Addendum"
            
            result = service.render_email_body("template.html", mock_process, "<table>test</table>")
            
            assert result == "<html>rendered content</html>"
            mock_template.render.assert_called_once()

    def test_create_html_table_success(self):
        """Test create_html_table with valid data"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            test_data = [
                {"Item ID": "123", "Title": "Test Book"},
                {"Item ID": "456", "Title": "Another Book"}
            ]
            
            mock_process = Mock()
            mock_process.email_subject = "Test Subject"
            
            with patch('alma_item_checks_notification_service.services.notification_service.pd') as mock_pd:
                mock_df = MagicMock()
                mock_df.empty = False
                mock_df.columns = ["Item ID", "Title"]  # Make columns iterable
                mock_df.__len__.return_value = 2  # Make len() work
                mock_df.to_html.return_value = "<table>test content</table>"
                mock_df.style.set_caption.return_value = mock_df
                mock_pd.read_json.return_value = mock_df
                
                result = service.create_html_table(test_data, mock_process)
                
                assert "<table>test content</table>" in result

    def test_create_html_table_with_zero_column_removal(self):
        """Test create_html_table removes zero column"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            mock_process = Mock()
            
            with patch('alma_item_checks_notification_service.services.notification_service.pd') as mock_pd:
                mock_df = MagicMock()
                mock_df.empty = False
                mock_df.columns = ["0", "Item ID"]  # Make columns iterable
                mock_df.__len__.return_value = 2  # Make len() work
                # Create mock for df['0'] chain
                mock_zero_column = Mock()
                mock_zero_column.astype.return_value.eq.return_value.all.return_value = True
                mock_df.__getitem__.return_value = mock_zero_column
                mock_df.drop = Mock()
                mock_df.to_html.return_value = "<table>no zero column</table>"
                mock_df.style.set_caption.return_value = mock_df
                mock_pd.read_json.return_value = mock_df
                
                result = service.create_html_table([{"test": "data"}], mock_process)
                
                mock_df.drop.assert_called_once_with("0", axis=1, inplace=True)

    def test_create_html_table_empty_dataframe(self):
        """Test create_html_table with empty DataFrame"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            mock_process = Mock()
            
            with patch('alma_item_checks_notification_service.services.notification_service.pd') as mock_pd:
                mock_df = MagicMock()
                mock_df.empty = True
                mock_df.columns = []  # Make columns iterable
                mock_df.__len__.return_value = 0  # Make len() work
                mock_df.style.set_caption.return_value = mock_df
                mock_pd.read_json.return_value = mock_df
                
                result = service.create_html_table([{"test": "data"}], mock_process)
                
                assert "Report generated, but contained no displayable data" in result

    def test_create_html_table_none_report(self):
        """Test create_html_table with None report"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                result = service.create_html_table(None, Mock())
                
                assert result is None
                mock_logging.warning.assert_called_with(
                    "NotificationService.create_html_table: No JSON data string available for conversion."
                )

    def test_create_html_table_conversion_exception(self):
        """Test create_html_table handles conversion exceptions"""
        with patch('alma_item_checks_notification_service.services.notification_service.StorageService'):
            service = NotificationService(self.mock_message)
            
            with patch('alma_item_checks_notification_service.services.notification_service.pd.read_json', 
                      side_effect=Exception("Conversion error")):
                with patch('alma_item_checks_notification_service.services.notification_service.logging') as mock_logging:
                    result = service.create_html_table([{"test": "data"}], Mock())
                    
                    assert "Error generating table from data" in result
                    assert any("Failed JSON->HTML conversion" in str(call) for call in mock_logging.error.call_args_list)