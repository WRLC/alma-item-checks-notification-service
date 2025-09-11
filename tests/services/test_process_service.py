"""Tests for ProcessService"""
import pytest
from unittest.mock import Mock, patch

from alma_item_checks_notification_service.services.process_service import ProcessService
from alma_item_checks_notification_service.repos.process_repo import ProcessRepository
from alma_item_checks_notification_service.models.process import Process


class TestProcessService:
    """Tests for ProcessService"""
    
    def test_init(self, db_session):
        """Test ProcessService initialization"""
        service = ProcessService(db_session)
        assert isinstance(service.process_repo, ProcessRepository)
        assert service.process_repo.session is db_session
    
    def test_get_process_id_by_name_success(self, db_session, sample_process):
        """Test get_process_id_by_name returns process ID for valid name"""
        service = ProcessService(db_session)
        
        process_id = service.get_process_id_by_name(sample_process.name)
        
        assert process_id == sample_process.id
    
    def test_get_process_id_by_name_not_found(self, db_session):
        """Test get_process_id_by_name returns None when process not found"""
        service = ProcessService(db_session)
        
        process_id = service.get_process_id_by_name("non_existent_process")
        
        assert process_id is None
    
    def test_get_process_id_by_name_calls_repo(self, db_session):
        """Test get_process_id_by_name calls repository method"""
        service = ProcessService(db_session)
        
        with patch.object(service.process_repo, 'get_process_id_by_name', return_value=123) as mock_get_id:
            result = service.get_process_id_by_name("test_process")
            
            mock_get_id.assert_called_once_with("test_process")
            assert result == 123
    
    def test_get_process_by_name_success(self, db_session, sample_process):
        """Test get_process_by_name returns process object for valid name"""
        service = ProcessService(db_session)
        
        process = service.get_process_by_name(sample_process.name)
        
        assert process is not None
        assert process.id == sample_process.id
        assert process.name == sample_process.name
        assert process.email_subject == sample_process.email_subject
    
    def test_get_process_by_name_not_found(self, db_session):
        """Test get_process_by_name returns None when process not found"""
        service = ProcessService(db_session)
        
        process = service.get_process_by_name("non_existent_process")
        
        assert process is None
    
    def test_get_process_by_name_calls_repo(self, db_session):
        """Test get_process_by_name calls repository method"""
        service = ProcessService(db_session)
        mock_process = Mock(spec=Process)
        
        with patch.object(service.process_repo, 'get_process_by_name', return_value=mock_process) as mock_get_process:
            result = service.get_process_by_name("test_process")
            
            mock_get_process.assert_called_once_with("test_process")
            assert result is mock_process
    
    def test_get_process_id_by_name_handles_repo_exception(self, db_session):
        """Test get_process_id_by_name handles repository exceptions"""
        service = ProcessService(db_session)
        
        with patch.object(service.process_repo, 'get_process_id_by_name', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                service.get_process_id_by_name("test_process")
    
    def test_get_process_by_name_handles_repo_exception(self, db_session):
        """Test get_process_by_name handles repository exceptions"""
        service = ProcessService(db_session)
        
        with patch.object(service.process_repo, 'get_process_by_name', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                service.get_process_by_name("test_process")
    
    def test_multiple_processes_service(self, db_session):
        """Test service methods work with multiple processes"""
        process1 = Process(
            name="process1",
            email_subject="Subject 1",
            email_body="Body 1",
            container="container1"
        )
        process2 = Process(
            name="process2",
            email_subject="Subject 2",
            email_body="Body 2", 
            container="container2"
        )
        db_session.add_all([process1, process2])
        db_session.commit()
        
        service = ProcessService(db_session)
        
        # Test get_process_id_by_name
        id1 = service.get_process_id_by_name("process1")
        id2 = service.get_process_id_by_name("process2")
        assert id1 == process1.id
        assert id2 == process2.id
        assert id1 != id2
        
        # Test get_process_by_name
        found_process1 = service.get_process_by_name("process1")
        found_process2 = service.get_process_by_name("process2")
        assert found_process1.name == "process1"
        assert found_process2.name == "process2"
        assert found_process1.id != found_process2.id