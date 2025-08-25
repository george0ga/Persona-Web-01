# tests/test_services.py
import pytest
from unittest.mock import Mock, patch
from app.services.check_service import CheckService
from app.services.status_manager import StatusManager

class TestCheckService:
    """Тесты для CheckService"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.service = CheckService(headless=True)
    
    def test_init(self):
        """Тест инициализации сервиса"""
        assert self.service.headless_mode is True
    
    @patch('services.check_service.parse_courts')
    def test_check_courts_success(self, mock_parse):
        """Тест успешной проверки судов"""
        mock_parse.return_value = {"result": "success"}
        
        from schemas.schemas import PersonInitials
        fullname = PersonInitials(surname="Иванов", name="Иван")
        
        result = self.service.check_courts("http://court.ru", fullname)
        assert result == {"result": "success"}
        mock_parse.assert_called_once_with("http://court.ru", fullname, True)
    
    @patch('services.check_service.parse_courts')
    def test_check_courts_error(self, mock_parse):
        """Тест ошибки при проверке судов"""
        mock_parse.side_effect = Exception("Parsing error")
        
        from schemas.schemas import PersonInitials
        fullname = PersonInitials(surname="Иванов", name="Иван")
        
        with pytest.raises(Exception, match="Parsing error"):
            self.service.check_courts("http://court.ru", fullname)

class TestStatusManager:
    """Тесты для StatusManager"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = StatusManager()
    
    def test_url_to_id(self):
        """Тест генерации ID из URL"""
        url = "http://court.ru"
        task_id = self.manager.url_to_id(url)
        assert isinstance(task_id, str)
        assert len(task_id) == 12
    
    def test_update_status(self):
        """Тест обновления статуса"""
        task_id = "test_123"
        status = "processing"
        person = "Иванов Иван"
        
        self.manager.update_status(task_id, status, person)
        
        assert self.manager.statuses[task_id]["status"] == status
        assert self.manager.statuses[task_id]["person"] == person
    
    def test_clear_statuses(self):
        """Тест очистки статусов"""
        self.manager.update_status("test1", "status1", "person1")
        self.manager.update_status("test2", "status2", "person2")
        
        assert len(self.manager.statuses) == 2
        
        self.manager.clear_statuses()
        assert len(self.manager.statuses) == 0