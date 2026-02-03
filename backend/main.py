import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация базы данных
if os.getenv("RENDER"):  # Проверяем, что мы на Render
    # Используем PostgreSQL от Render
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Локально используем SQLite
    DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Модель данных
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Integer, default=0)  # 0 = не выполнено, 1 = выполнено


# Создаем таблицы
Base.metadata.create_all(bind=engine)


# Pydantic схемы
class TaskCreate(BaseModel):
    title: str
    description: str = ""


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: int

    class Config:
        from_attributes = True


# FastAPI приложение
app = FastAPI(title="My SPA App", version="1.0.0")

# CORS для доступа с любых доменов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздаем статику фронтенда
# В Render фронтенд будет в отдельном сервисе, но для простоты можно и так
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API эндпоинты
@app.get("/")
async def root():
    """Главная страница - отдаем SPA"""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "API работает! Перейдите на /docs для документации"}


@app.get("/api/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy", "service": "my-spa-app", "environment": os.getenv("RENDER_ENV", "development")}


@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    """Получить все задачи"""
    tasks = db.query(Task).all()
    return tasks


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Создать новую задачу"""
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    logger.info(f"Создана задача: {db_task.id}")
    return db_task


@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    """Обновить задачу"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    db_task.title = task.title
    db_task.description = task.description
    db.commit()
    return {"message": "Задача обновлена", "task_id": task_id}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Удалить задачу"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    db.delete(db_task)
    db.commit()
    return {"message": "Задача удалена", "task_id": task_id}


@app.get("/api/version")
async def get_version():
    """Получить версию приложения"""
    return {
        "version": "1.0.0",
        "framework": "FastAPI",
        "database": "PostgreSQL" if os.getenv("RENDER") else "SQLite"
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)