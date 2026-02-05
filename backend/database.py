# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import ssl

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Для Render PostgreSQL
    # Преобразуем URL для psycopg2
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

    # Создаем SSL контекст
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Отключаем проверку сертификата
    connect_args = {
        # Вариант 1: Самый простой (часто работает)
        "sslmode": "require",

        # ИЛИ Вариант 2: Без проверки хоста
        # "sslmode": "verify-ca",
        # "sslrootcert": "",

        # ИЛИ Вариант 3: Без SSL (опасно, только для теста)
        # "sslmode": "disable",
    }
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "sslmode": "require",
            "sslrootcert": "",  # Пустая строка для автоматического определения
            "ssl": ssl_context,  # Явно передаем SSL контекст
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
else:
    # Fallback на SQLite
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()