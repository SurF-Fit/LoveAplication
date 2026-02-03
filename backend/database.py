import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Критически важно для Render!
DATABASE_URL = os.getenv("DATABASE_URL")

# Render использует postgres://, но SQLAlchemy требует postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Для локальной разработки
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./loveapp.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()