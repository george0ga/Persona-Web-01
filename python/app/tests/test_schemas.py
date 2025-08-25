# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas.schemas import PersonInitials, CourtCheckModel, CourtVerifyModel

class TestPersonInitials:
    """Тесты для модели PersonInitials"""
    
    def test_valid_person_initials(self):
        """Тест валидных ФИО"""
        data = {
            "surname": "Иванов",
            "name": "Иван",
            "patronymic": "Иванович"
        }
        person = PersonInitials(**data)
        assert person.surname == "Иванов"
        assert person.name == "Иван"
        assert person.patronymic == "Иванович"
    
    def test_person_without_patronymic(self):
        """Тест ФИО без отчества"""
        data = {
            "surname": "Петров",
            "name": "Петр"
        }
        person = PersonInitials(**data)
        assert person.patronymic is None
    
    def test_empty_surname(self):
        """Тест пустой фамилии"""
        data = {
            "surname": "",
            "name": "Иван"
        }
        with pytest.raises(ValidationError):
            PersonInitials(**data)
    
    def test_short_name(self):
        """Тест слишком короткого имени"""
        data = {
            "surname": "Иванов",
            "name": "А"
        }
        with pytest.raises(ValidationError):
            PersonInitials(**data)
    
    def test_invalid_characters(self):
        """Тест недопустимых символов"""
        data = {
            "surname": "Иванов123",
            "name": "Иван"
        }
        with pytest.raises(ValidationError):
            PersonInitials(**data)

class TestCourtCheckModel:
    """Тесты для модели CourtCheckModel"""
    
    def test_valid_single_address(self):
        """Тест валидного одиночного адреса"""
        data = {
            "address": "http://court.ru",
            "fullname": {
                "surname": "Иванов",
                "name": "Иван"
            }
        }
        court = CourtCheckModel(**data)
        assert court.address == "http://court.ru"
    
    def test_valid_multiple_addresses(self):
        """Тест валидных множественных адресов"""
        data = {
            "address": ["http://court1.ru", "http://court2.ru"],
            "fullname": {
                "surname": "Иванов",
                "name": "Иван"
            }
        }
        court = CourtCheckModel(**data)
        assert len(court.address) == 2
    
    def test_invalid_protocol(self):
        """Тест неверного протокола"""
        data = {
            "address": "ftp://court.ru",
            "fullname": {
                "surname": "Иванов",
                "name": "Иван"
            }
        }
        with pytest.raises(ValidationError):
            CourtCheckModel(**data)
    
    def test_empty_address_list(self):
        """Тест пустого списка адресов"""
        data = {
            "address": [],
            "fullname": {
                "surname": "Иванов",
                "name": "Иван"
            }
        }
        with pytest.raises(ValidationError):
            CourtCheckModel(**data)
    
    def test_too_many_addresses(self):
        """Тест слишком большого количества адресов"""
        addresses = [f"http://court{i}.ru" for i in range(15)]
        data = {
            "address": addresses,
            "fullname": {
                "surname": "Иванов",
                "name": "Иван"
            }
        }
        with pytest.raises(ValidationError):
            CourtCheckModel(**data)