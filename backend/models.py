from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    gender = Column(String(10), nullable=False)  # "male" или "female"
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    couple_id = Column(Integer, ForeignKey("couples.id"), nullable=True)
    couple = relationship("Couple", back_populates="partners")
    test_results = relationship("TestResult", back_populates="user")
    love_messages = relationship("LoveMessage", back_populates="user")


class Couple(Base):
    __tablename__ = "couples"

    id = Column(Integer, primary_key=True, index=True)
    couple_code = Column(String(10), unique=True, nullable=False)
    relationship_name = Column(String(100), default="Наша пара")
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Связи
    partners = relationship("User", back_populates="couple")
    tests = relationship("Test", back_populates="couple")
    shared_results = relationship("SharedTestResult", back_populates="couple")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # "love", "compatibility", "future"
    questions = Column(JSON, nullable=False)  # Список вопросов в JSON
    couple_id = Column(Integer, ForeignKey("couples.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    couple = relationship("Couple", back_populates="tests")
    results = relationship("TestResult", back_populates="test")
    shared_results = relationship("SharedTestResult", back_populates="test")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    answers = Column(JSON, nullable=False)  # Ответы пользователя
    score = Column(Integer, nullable=False)
    interpretation = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="test_results")
    test = relationship("Test", back_populates="results")


class SharedTestResult(Base):
    __tablename__ = "shared_test_results"

    id = Column(Integer, primary_key=True, index=True)
    couple_id = Column(Integer, ForeignKey("couples.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    combined_score = Column(Integer, nullable=False)
    compatibility_percentage = Column(Integer, nullable=False)
    insights = Column(JSON, nullable=False)  # Общие выводы
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    couple = relationship("Couple", back_populates="shared_results")
    test = relationship("Test", back_populates="shared_results")


class LoveMessage(Base):
    __tablename__ = "love_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    couple_id = Column(Integer, ForeignKey("couples.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="love_messages")