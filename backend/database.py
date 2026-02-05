import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Критически важно для Render!
DATABASE_URL = os.getenv("DATABASE_URL")

# Render использует postgres://, но SQLAlchemy требует postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Для PostgreSQL - настраиваем пул соединений
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,  # Используем пул очереди

        # Оптимальные настройки для Render.com
        pool_size=5,  # Максимум соединений в пуле
        max_overflow=10,  # Максимум дополнительных соединений
        pool_timeout=30,  # Таймаут ожидания соединения
        pool_recycle=300,  # Пересоздавать соединения каждые 5 минут
        pool_pre_ping=True,  # Проверять соединение перед использованием

        connect_args={
            "sslmode": "require",
            "connect_timeout": 10
        },

        # Для продакшена
        echo=False,  # Не логировать SQL (только для дебага)
    )
else:
    # Fallback для разработки
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
# Для локальной разработки
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./loveapp.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Важно для производительности
)
Base = declarative_base()