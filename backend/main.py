from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid
import json
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import hashlib

# Импорт моделей и схем
from models import Base, User, Couple, Test, TestResult, SharedTestResult, LoveMessage
from database import engine, SessionLocal
from schemas import (
    UserCreate, UserResponse, UserLogin,
    CoupleCreate, CoupleResponse,
    TestCreate, TestResponse, TestQuestion,
    TestAnswer, TestResultResponse,
    SharedResultResponse, LoveMessageCreate,
    Token, TokenData
)
from sqlalchemy import text


# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Love Application", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://loveaplication-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Кэшировать preflight на 10 минут
)

# Настройки
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "django_argon2", "django_bcrypt"],
    deprecated="auto"
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Директория для загрузки файлов
UPLOAD_DIR = "uploads"
AVATAR_DIR = os.path.join(UPLOAD_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

def grant_permissions():
    """Дать права пользователю loveapp_user"""
    with Session(engine) as session:
        # Даем все права
        session.execute(text("GRANT ALL ON SCHEMA public TO loveapp_user;"))
        session.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO loveapp_user;"))
        session.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO loveapp_user;"))
        session.commit()
        print("✅ Права выданы!")

# Dependency для БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Вспомогательные функции
def get_password_hash(password: str) -> str:
    """Простое хеширование SHA256 (устраняет проблему bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Простая проверка пароля"""
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user


# Функция для генерации кода пары
def generate_couple_code():
    return str(uuid.uuid4())[:8].upper()


# =========== CORS FIX: OPTIONS HANDLER ===========
from fastapi import Request


@app.get("/admin/init-db")
def init_db():
    """Инициализация БД через веб-интерфейс"""
    from sqlalchemy import text
    from database import engine

    with engine.connect() as conn:
        # Создаем таблицы
        # ... ваш код создания таблиц

        # Даем права
        conn.execute(text("GRANT ALL ON SCHEMA public TO loveapp_user;"))
        conn.commit()

    return {"message": "База данных инициализирована"}

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)

    # Разрешаем только ваш фронтенд
    allowed_origin = "https://loveaplication-frontend.onrender.com"

    # Проверяем Origin заголовок
    origin = request.headers.get("origin")
    if origin == allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    # Обязательные заголовки для CORS
    if request.method == "OPTIONS":
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "600"

    return response


# Явные обработчики OPTIONS для /register и /login
@app.options("/register")
@app.options("/login")
async def options_handler():
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://loveaplication-frontend.onrender.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600"
        }
    )


# ==================== Аутентификация ====================

@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, есть ли уже пользователь с таким email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # Создаем пользователя
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        gender=user_data.gender
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

class LoginForm(BaseModel):
    username: str
    password: str


@app.post("/login", response_model=Token)
async def login(login_data: LoginForm, db: Session = Depends(get_db)):
    # Ищем пользователя по email (который приходит как username)
    user = db.query(User).filter(User.email == login_data.username).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ==================== Профиль и аватар ====================

@app.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/upload-avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Проверяем тип файла
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Можно загружать только изображения")

    # Генерируем уникальное имя файла
    file_ext = file.filename.split(".")[-1]
    filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}.{file_ext}"
    file_path = os.path.join(AVATAR_DIR, filename)

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Обновляем URL аватара в базе
    avatar_url = f"/uploads/avatars/{filename}"
    current_user.avatar_url = avatar_url
    db.commit()

    return {"avatar_url": avatar_url, "message": "Аватар успешно загружен"}


# ==================== Пары ====================

@app.post("/couples/create")
async def create_couple(
        couple_name: str = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Проверяем, что у пользователя еще нет пары
    if current_user.couple_id:
        raise HTTPException(status_code=400, detail="Вы уже состоите в паре")

    # Создаем пару
    couple = Couple(
        couple_code=generate_couple_code(),
        relationship_name=couple_name,
        created_at=datetime.utcnow()
    )

    db.add(couple)
    db.flush()

    # Привязываем пользователя к паре
    current_user.couple_id = couple.id
    db.commit()
    db.refresh(couple)

    return {
        "couple_id": couple.id,
        "couple_code": couple.couple_code,
        "message": "Пара создана. Поделитесь кодом с партнером"
    }


@app.post("/couples/join")
async def join_couple(
        couple_code: str = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Проверяем, что у пользователя еще нет пары
    if current_user.couple_id:
        raise HTTPException(status_code=400, detail="Вы уже состоите в паре")

    # Находим пару по коду
    couple = db.query(Couple).filter(Couple.couple_code == couple_code).first()
    if not couple:
        raise HTTPException(status_code=404, detail="Пара с таким кодом не найдена")

    # Проверяем, что в паре есть место (максимум 2 человека)
    partner_count = db.query(User).filter(User.couple_id == couple.id).count()
    if partner_count >= 2:
        raise HTTPException(status_code=400, detail="В этой паре уже есть двое участников")

    # Привязываем пользователя к паре
    current_user.couple_id = couple.id
    db.commit()

    return {
        "couple_id": couple.id,
        "relationship_name": couple.relationship_name,
        "message": "Вы успешно присоединились к паре"
    }


@app.get("/couples/my", response_model=CoupleResponse)
async def get_my_couple(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not current_user.couple_id:
        raise HTTPException(status_code=404, detail="Вы не состоите в паре")

    couple = db.query(Couple).filter(Couple.id == current_user.couple_id).first()

    # Получаем информацию о партнере
    partners = db.query(User).filter(User.couple_id == couple.id).all()
    partner_info = []
    for partner in partners:
        partner_info.append({
            "id": partner.id,
            "username": partner.username,
            "gender": partner.gender,
            "avatar_url": partner.avatar_url
        })

    return {
        "id": couple.id,
        "couple_code": couple.couple_code,
        "relationship_name": couple.relationship_name,
        "avatar_url": couple.avatar_url,
        "created_at": couple.created_at,
        "partners": partner_info
    }


# ==================== Тесты ====================

# Предзаполненные тесты
DEFAULT_TESTS = [
    {
        "title": "Тест на совместимость",
        "description": "Узнайте, насколько вы подходите друг другу",
        "category": "compatibility",
        "questions": [
            {"id": 1, "text": "Насколько вы цените время, проведенное вместе?", "options": [
                {"value": 1, "text": "Не очень"},
                {"value": 2, "text": "Иногда"},
                {"value": 3, "text": "Часто"},
                {"value": 4, "text": "Очень"}
            ]},
            {"id": 2, "text": "Как часто вы обсуждаете будущее?", "options": [
                {"value": 1, "text": "Никогда"},
                {"value": 2, "text": "Редко"},
                {"value": 3, "text": "Иногда"},
                {"value": 4, "text": "Часто"}
            ]}
        ]
    },
    {
        "title": "Тест на любовные языки",
        "description": "Определите ваши языки любви",
        "category": "love",
        "questions": [
            {"id": 1, "text": "Что для вас важнее в отношениях?", "options": [
                {"value": "words", "text": "Слова поддержки"},
                {"value": "time", "text": "Время вместе"},
                {"value": "gifts", "text": "Подарки"},
                {"value": "touch", "text": "Физический контакт"}
            ]}
        ]
    }
]


@app.get("/tests/available")
async def get_available_tests(current_user: User = Depends(get_current_user)):
    return DEFAULT_TESTS


@app.post("/tests/start")
async def start_test(
        test_title: str = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Находим тест по названию
    test_data = next((t for t in DEFAULT_TESTS if t["title"] == test_title), None)
    if not test_data:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Проверяем, что пользователь в паре
    if not current_user.couple_id:
        raise HTTPException(status_code=400, detail="Для прохождения теста нужно быть в паре")

    # Создаем запись теста
    test = Test(
        title=test_data["title"],
        description=test_data["description"],
        category=test_data["category"],
        questions=json.dumps(test_data["questions"]),
        couple_id=current_user.couple_id,
        created_by=current_user.id
    )

    db.add(test)
    db.commit()
    db.refresh(test)

    return {
        "test_id": test.id,
        "title": test.title,
        "questions": json.loads(test.questions)
    }


@app.post("/tests/{test_id}/submit")
async def submit_test(
        test_id: int,
        answers: List[TestAnswer],
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Получаем тест
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Проверяем доступ
    if test.couple_id != current_user.couple_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому тесту")

    # Вычисляем результат
    score = 0
    for answer in answers:
        # Простая логика подсчета очков
        if isinstance(answer.answer_value, int):
            score += answer.answer_value
        else:
            score += 1

    # Интерпретация результата
    interpretation = ""
    if score < 3:
        interpretation = "Есть над чем поработать"
    elif score < 6:
        interpretation = "Хороший результат"
    else:
        interpretation = "Отличная совместимость!"

    # Сохраняем результат
    result = TestResult(
        user_id=current_user.id,
        test_id=test_id,
        answers=json.dumps([a.dict() for a in answers]),
        score=score,
        interpretation=interpretation
    )

    db.add(result)
    db.commit()

    # Проверяем, прошел ли партнер тест
    partner = db.query(User).filter(
        User.couple_id == current_user.couple_id,
        User.id != current_user.id
    ).first()

    partner_result = db.query(TestResult).filter(
        TestResult.test_id == test_id,
        TestResult.user_id == partner.id
    ).first() if partner else None

    # Если оба прошли тест, создаем общий результат
    if partner_result:
        combined_score = (score + partner_result.score) / 2
        compatibility = min(int((combined_score / 8) * 100), 100)

        shared_result = SharedTestResult(
            couple_id=current_user.couple_id,
            test_id=test_id,
            combined_score=int(combined_score),
            compatibility_percentage=compatibility,
            insights=json.dumps({
                "user1_score": score,
                "user2_score": partner_result.score,
                "comparison": "Ваши результаты хорошо дополняют друг друга" if abs(
                    score - partner_result.score) <= 2 else "Есть различия в подходах"
            })
        )

        db.add(shared_result)
        db.commit()

    return {
        "score": score,
        "interpretation": interpretation,
        "message": "Результат сохранен. Ожидайте результаты партнера."
    }


@app.get("/tests/results")
async def get_test_results(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Личные результаты
    personal_results = db.query(TestResult).filter(
        TestResult.user_id == current_user.id
    ).all()

    # Общие результаты пары
    shared_results = []
    if current_user.couple_id:
        shared_results = db.query(SharedTestResult).filter(
            SharedTestResult.couple_id == current_user.couple_id
        ).all()

    return {
        "personal": [
            {
                "test_title": result.test.title,
                "score": result.score,
                "interpretation": result.interpretation,
                "completed_at": result.completed_at
            }
            for result in personal_results
        ],
        "shared": [
            {
                "test_title": result.test.title,
                "compatibility_percentage": result.compatibility_percentage,
                "combined_score": result.combined_score,
                "created_at": result.created_at
            }
            for result in shared_results
        ]
    }


# ==================== Сообщения ====================

@app.post("/messages/send")
async def send_message(
        message_data: LoveMessageCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not current_user.couple_id:
        raise HTTPException(status_code=400, detail="Нужно быть в паре")

    message = LoveMessage(
        user_id=current_user.id,
        couple_id=current_user.couple_id,
        message=message_data.message,
        is_anonymous=message_data.is_anonymous
    )

    db.add(message)
    db.commit()

    return {"message": "Сообщение отправлено", "message_id": message.id}


@app.get("/messages")
async def get_messages(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not current_user.couple_id:
        return []

    messages = db.query(LoveMessage).filter(
        LoveMessage.couple_id == current_user.couple_id
    ).order_by(LoveMessage.created_at.desc()).limit(50).all()

    return [
        {
            "id": msg.id,
            "username": "Аноним" if msg.is_anonymous else msg.user.username,
            "message": msg.message,
            "created_at": msg.created_at,
            "is_yours": msg.user_id == current_user.id
        }
        for msg in messages
    ]


# ==================== Статистика ====================

@app.get("/stats")
async def get_couple_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not current_user.couple_id:
        raise HTTPException(status_code=400, detail="Нужно быть в паре")

    # Количество пройденных тестов
    test_count = db.query(TestResult).filter(
        TestResult.user_id == current_user.id
    ).count()

    # Средняя совместимость
    shared_results = db.query(SharedTestResult).filter(
        SharedTestResult.couple_id == current_user.couple_id
    ).all()

    avg_compatibility = 0
    if shared_results:
        avg_compatibility = sum(r.compatibility_percentage for r in shared_results) / len(shared_results)

    # Количество сообщений
    message_count = db.query(LoveMessage).filter(
        LoveMessage.couple_id == current_user.couple_id
    ).count()

    # Партнер
    partner = db.query(User).filter(
        User.couple_id == current_user.couple_id,
        User.id != current_user.id
    ).first()

    partner_name = partner.username if partner else "Ожидание партнера"

    return {
        "test_count": test_count,
        "avg_compatibility": round(avg_compatibility, 1),
        "message_count": message_count,
        "partner_name": partner_name,
        "together_since": current_user.couple.created_at if current_user.couple else None
    }


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Love Application"}


@app.get("/debug/db-info")
async def debug_db_info(db: Session = Depends(get_db)):
    """Информация о БД и пользователях"""

    # Проверка подключения
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Получаем пользователей
    users = []
    try:
        user_records = db.query(User).all()
        for u in user_records:
            users.append({
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "hash_length": len(u.password_hash) if u.password_hash else 0,
                "hash_preview": u.password_hash[:20] + "..." if u.password_hash else None,
                "created_at": str(u.created_at) if u.created_at else None
            })
    except Exception as e:
        users = f"error: {str(e)}"

    # Проверяем переменные окружения
    import os
    return {
        "database_url_exists": bool(os.getenv("DATABASE_URL")),
        "database_url_preview": os.getenv("DATABASE_URL", "not found")[:50] + "..." if os.getenv(
            "DATABASE_URL") else None,
        "db_status": db_status,
        "user_count": len(user_records) if isinstance(users, list) else 0,
        "users": users
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)