from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


# Пользователь
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    gender: str  # "male" или "female"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    gender: str
    avatar_url: Optional[str]
    couple_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Пары
class CoupleCreate(BaseModel):
    relationship_name: str


class CoupleResponse(BaseModel):
    id: int
    couple_code: str
    relationship_name: str
    avatar_url: Optional[str]
    created_at: datetime
    partners: List[Dict[str, Any]]


# Тесты
class TestQuestion(BaseModel):
    id: int
    text: str
    options: List[Dict[str, Any]]


class TestAnswer(BaseModel):
    question_id: int
    answer_value: Any


class TestCreate(BaseModel):
    title: str
    description: Optional[str]
    category: str
    questions: List[TestQuestion]


class TestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    questions: List[TestQuestion]
    created_at: datetime


# Результаты тестов
class TestResultResponse(BaseModel):
    id: int
    score: int
    interpretation: Optional[str]
    completed_at: datetime


class SharedResultResponse(BaseModel):
    id: int
    compatibility_percentage: int
    combined_score: int
    insights: Dict[str, Any]
    created_at: datetime


# Сообщения
class LoveMessageCreate(BaseModel):
    message: str
    is_anonymous: bool = False


class LoveMessageResponse(BaseModel):
    id: int
    username: str
    message: str
    created_at: datetime
    is_yours: bool


# Токены
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None