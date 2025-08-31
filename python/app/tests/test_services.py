import pytest
from unittest.mock import Mock, patch
from app.services.check_service import CheckService
from app.config.settings import settings

class TestCheckService:
    """Тесты для CheckService"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.service = CheckService(headless=settings.HEADLESS)

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
