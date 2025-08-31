from pydantic import BaseModel, field_validator
from typing import Optional, List, Union, Literal, Any
import re

class PersonInitials(BaseModel):
    surname: str
    name: Optional[str] = None
    patronymic: Optional[str] = None
    
    @field_validator('surname')
    @classmethod
    def validate_surname(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Фамилия не может быть пустой')
        if len(v.strip()) < 2:
            raise ValueError('Фамилия должна содержать минимум 2 символа')
        if len(v.strip()) > 50:
            raise ValueError('Фамилия слишком длинная (максимум 50 символов)')
        if not re.match(r'^[а-яёА-ЯЁa-zA-Z\s\-]+$', v.strip()):
            raise ValueError('Фамилия должна содержать только буквы, пробелы и дефисы')
        return v.strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        if len(v.strip()) < 2:
            raise ValueError('Имя должно содержать минимум 2 символа')
        if len(v.strip()) > 50:
            raise ValueError('Имя слишком длинное (максимум 50 символов)')
        if not re.match(r'^[а-яёА-ЯЁa-zA-Z\s\-]+$', v.strip()):
            raise ValueError('Имя должно содержать только буквы, пробелы и дефисы')
        return v.strip()
    
    @field_validator('patronymic')
    @classmethod
    def validate_patronymic(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        if len(v.strip()) < 2:
            raise ValueError('Отчество должно содержать минимум 2 символа')
        if len(v.strip()) > 50:
            raise ValueError('Отчество слишком длинное (максимум 50 символов)')
        if not re.match(r'^[а-яёА-ЯЁa-zA-Z\s\-]+$', v.strip()):
            raise ValueError('Отчество должно содержать только буквы, пробелы и дефисы')
        return v.strip()

class CourtResponseModel(BaseModel):
    success: bool
    status: Literal["success", "error", "queued", "format_error", "server_error"]
    message: str
    data: Optional[Any] = None

class CourtCheckModel(BaseModel):
    address: Union[str, List[str]]
    fullname: PersonInitials

class CourtVerifyModel(BaseModel):
    address: Union[str, List[str]]

class QueueSizeResponseModel(BaseModel):
    redis_check_courts_queue_size: int
    redis_verify_courts_queue_size: int
    celery_check_courts_queue_size: int
    celery_verify_courts_queue_size: int
    celery_court_last_check_time_blue: float
    celery_court_last_check_time_yellow: float