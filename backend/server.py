"""
UniSoruyor.com - Supabase Backend
Modern, modular backend with Supabase integration
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import jwt
import os
import uuid
import re
import json

# Local imports
from dotenv import load_dotenv
from database import db
from supabase_client import supabase_admin
from storage import storage

load_dotenv()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# =========================================
# Pydantic Models
# =========================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    university: str
    faculty: str
    department: str
    isYKSStudent: bool = False

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    university: str
    faculty: str
    department: str
    is_admin: bool = False
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class QuestionCreate(BaseModel):
    title: str
    content: str
    category: str

class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class AnswerCreate(BaseModel):
    question_id: str
    content: str
    parent_answer_id: Optional[str] = None

class AnswerUpdate(BaseModel):
    content: str

# =========================================
# Profanity Filter
# =========================================

PROFANITY_WORDS = [
    # Turkish profanity
    'amk', 'aq', 'sik', 'sikerim', 'siktir', 'siktirgit', 'göt', 'götünü', 'götün', 'götveren',
    'orospu', 'orospuçocuğu', 'orospucogu', 'orospucoqu', 'oç', 'piç', 'pıç', 'it', 'kaltak', 'kahpe', 'pezevenk', 
    'ibne', 'ibnelik', 'ıbne', 'ıbnesi', 'ıbnelik', 'top', 'gavat', 'gavur', 'puşt', 
    'yarrak', 'yarrağım', 'yarak', 'yarrağını', 'yarragım', 'yarragin', 'yarrakın', 'yarraginı', 'yarraq', 'yarraqsız',
    'annesini', 'babasını', 'ananı', 'avradını', 'ananıskm', 'amına', 'amını', 'amına koyayım', 'amına kodum', 
    'şerefsiz', 'şerefsız', 'şerefsızlık', 'namussuz', 'haysiyetsiz', 'haysıyet', 'haysıyetsız',
    'gerizekalı', 'gerızekalı', 'gerızekalılık', 'adi', 'sahtekar', 'yalancı', 'oe',
    'sıçmak', 'sıçar', 'sıçam', 'sıkerim', 'sıker', 'sıkme', 'sıktır', 'sıktırmak',
]

PROFANITY_PATTERNS = [
    (r'\b(a[\W_]*m[\W_]*k)\b', 'amk'),
    (r'(a[\W_]*n[\W_]*a[\W_]*n[\W_]*ı[\W_]*s[\W_]*k[\W_]*m)', 'ananıskm'),
    (r'(o[\W_]*ç)', 'oç'),
    (r'(o[\W_]*r[\W_]*o[\W_]*s[\W_]*p[\W_]*u)', 'orospu'),
]

def contains_profanity(text: str) -> tuple:
    """Check if text contains profanity"""
    text_lower = text.lower()
    
    for word in PROFANITY_WORDS:
        if word.lower() in text_lower:
            return True, word
    
    for pattern, word in PROFANITY_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True, word
    
    return False, ""

def extract_mentions(content: str) -> List[str]:
    """Extract @username mentions from content"""
    mentions = re.findall(r'@(\w+)', content)
    return list(set(mentions))

# =========================================
# Authentication Helpers
# =========================================

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        user = await db.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# =========================================
# Rate Limiting Helper
# =========================================

async def check_rate_limit(user_id: str, action_type: str = "question") -> bool:
    """Check if user can perform action (simple rate limiting)"""
    user = await db.get_user_by_id(user_id)
    if not user:
        return False
    
    last_action_field = f"last_{action_type}_at"
    last_action = user.get(last_action_field)
    
    if last_action:
        # Parse datetime
        if isinstance(last_action, str):
            last_action_dt = datetime.fromisoformat(last_action.replace('Z', '+00:00'))
        else:
            last_action_dt = last_action
        
        # Check if 2 minutes have passed
        now = datetime.utcnow()
        time_diff = (now - last_action_dt.replace(tzinfo=None)).total_seconds()
        
        if time_diff < 120:  # 2 minutes
            return False
    
    return True

# =========================================
# Initialize FastAPI
# =========================================

app = FastAPI(
    title="UniSoruyor.com API",
    description="Türkiye'nin en büyük üniversite öğrenci topluluğu - Supabase Backend",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# Health Check
# =========================================

@app.get("/")
async def root():
    return {
        "message": "UniSoruyor.com API - Supabase Edition",
        "version": "3.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "supabase",
        "timestamp": datetime.utcnow().isoformat()
    }

# =========================================
# Authentication Endpoints
# =========================================

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check for profanity in username
    username_has_profanity, found_word = contains_profanity(user_data.username)
    if username_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"Kullanıcı adı uygunsuz kelime içeriyor: '{found_word}'"
        )
    
    # Check if email already exists
    existing_email = await db.get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Bu e-posta adresi zaten kullanılıyor"
        )
    
    # Check if username already exists
    existing_username = await db.get_user_by_username(user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Bu kullanıcı adı zaten kullanılıyor"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(user_data.password)
    
    new_user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "university": user_data.university,
        "faculty": user_data.faculty,
        "department": user_data.department,
        "password_hash": password_hash,
        "is_admin": False,
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        created_user = await db.create_user(new_user)
        if not created_user:
            raise HTTPException(status_code=500, detail="Kullanıcı oluşturulamadı")
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        user_response = UserResponse(
            id=created_user["id"],
            username=created_user["username"],
            email=created_user["email"],
            university=created_user["university"],
            faculty=created_user["faculty"],
            department=created_user["department"],
            is_admin=created_user.get("is_admin", False),
            created_at=created_user["created_at"]
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user"""
    # Check by email or username
    user = await db.get_user_by_email(user_credentials.email_or_username)
    if not user:
        user = await db.get_user_by_username(user_credentials.email_or_username)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Mail adresi/kullanıcı adı veya şifre hatalı"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Mail adresi/kullanıcı adı veya şifre hatalı"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    user_response = UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        university=user["university"],
        faculty=user["faculty"],
        department=user["department"],
        is_admin=user.get("is_admin", False),
        created_at=user["created_at"]
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

# =========================================
# Question Endpoints
# =========================================

@app.post("/api/questions")
async def create_question(
    question_data: QuestionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new question"""
    # Check rate limit
    can_post = await check_rate_limit(current_user["id"], "question")
    if not can_post:
        raise HTTPException(
            status_code=429,
            detail="Çok sık soru soruyorsunuz. Lütfen 2 dakika bekleyin."
        )
    
    # Check for profanity
    title_has_profanity, found_word = contains_profanity(question_data.title)
    if title_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"Başlık uygunsuz kelime içeriyor: '{found_word}'"
        )
    
    content_has_profanity, found_word = contains_profanity(question_data.content)
    if content_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"İçerik uygunsuz kelime içeriyor: '{found_word}'"
        )
    
    # Create question
    question_id = str(uuid.uuid4())
    new_question = {
        "id": question_id,
        "title": question_data.title,
        "content": question_data.content,
        "author_id": current_user["id"],
        "author_username": current_user["username"],
        "author_university": current_user["university"],
        "author_faculty": current_user["faculty"],
        "author_department": current_user["department"],
        "category": question_data.category,
        "created_at": datetime.utcnow().isoformat(),
        "view_count": 0,
        "answer_count": 0,
        "like_count": 0
    }
    
    try:
        created_question = await db.create_question(new_question)
        if not created_question:
            raise HTTPException(status_code=500, detail="Soru oluşturulamadı")
        
        # Update user's last question time
        await db.update_user_last_question(current_user["id"])
        
        return created_question
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions")
async def get_questions(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all questions with optional filtering"""
    try:
        questions = await db.get_questions(
            limit=limit,
            offset=offset,
            category=category,
            search=search
        )
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions/{question_id}")
async def get_question(question_id: str):
    """Get a single question by ID"""
    question = await db.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    # Increment view count
    await db.increment_question_views(question_id)
    
    # Get answers
    answers = await db.get_answers_by_question(question_id)
    
    return {
        "question": question,
        "answers": answers
    }

@app.put("/api/questions/{question_id}")
async def update_question(
    question_id: str,
    question_update: QuestionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a question"""
    question = await db.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    # Check ownership
    if question["author_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Bu soruyu düzenleme yetkiniz yok")
    
    # Check for profanity if updating
    if question_update.title:
        title_has_profanity, found_word = contains_profanity(question_update.title)
        if title_has_profanity:
            raise HTTPException(
                status_code=400,
                detail=f"Başlık uygunsuz kelime içeriyor: '{found_word}'"
            )
    
    if question_update.content:
        content_has_profanity, found_word = contains_profanity(question_update.content)
        if content_has_profanity:
            raise HTTPException(
                status_code=400,
                detail=f"İçerik uygunsuz kelime içeriyor: '{found_word}'"
            )
    
    # Update question
    update_data = {}
    if question_update.title:
        update_data["title"] = question_update.title
    if question_update.content:
        update_data["content"] = question_update.content
    
    success = await db.update_question(question_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Soru güncellenemedi")
    
    updated_question = await db.get_question_by_id(question_id)
    return updated_question

@app.delete("/api/questions/{question_id}")
async def delete_question(
    question_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a question"""
    question = await db.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    # Check ownership
    if question["author_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Bu soruyu silme yetkiniz yok")
    
    success = await db.delete_question(question_id)
    if not success:
        raise HTTPException(status_code=500, detail="Soru silinemedi")
    
    return {"message": "Soru başarıyla silindi"}

# =========================================
# Answer Endpoints
# =========================================

@app.post("/api/answers")
async def create_answer(
    answer_data: AnswerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new answer"""
    # Check rate limit
    can_post = await check_rate_limit(current_user["id"], "answer")
    if not can_post:
        raise HTTPException(
            status_code=429,
            detail="Çok sık cevap gönderiyorsunuz. Lütfen 2 dakika bekleyin."
        )
    
    # Check for profanity
    content_has_profanity, found_word = contains_profanity(answer_data.content)
    if content_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"İçerik uygunsuz kelime içeriyor: '{found_word}'"
        )
    
    # Check if question exists
    question = await db.get_question_by_id(answer_data.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    # Extract mentions
    mentions = extract_mentions(answer_data.content)
    
    # Create answer
    answer_id = str(uuid.uuid4())
    new_answer = {
        "id": answer_id,
        "question_id": answer_data.question_id,
        "content": answer_data.content,
        "author_id": current_user["id"],
        "author_username": current_user["username"],
        "mentioned_users": json.dumps(mentions) if mentions else None,
        "parent_answer_id": answer_data.parent_answer_id,
        "created_at": datetime.utcnow().isoformat(),
        "is_accepted": False,
        "reply_count": 0
    }
    
    try:
        created_answer = await db.create_answer(new_answer)
        if not created_answer:
            raise HTTPException(status_code=500, detail="Cevap oluşturulamadı")
        
        # Update user's last answer time
        await db.update_user_last_answer(current_user["id"])
        
        # Create notification for question author
        if question["author_id"] != current_user["id"]:
            notification_data = {
                "id": str(uuid.uuid4()),
                "user_id": question["author_id"],
                "type": "answer",
                "title": "Sorunuza yeni cevap",
                "message": f"{current_user['username']} sorunuza cevap verdi",
                "related_question_id": answer_data.question_id,
                "related_answer_id": answer_id,
                "from_user_id": current_user["id"],
                "from_username": current_user["username"],
                "is_read": False,
                "created_at": datetime.utcnow().isoformat()
            }
            await db.create_notification(notification_data)
        
        # Create notifications for mentioned users
        for mention in mentions:
            mentioned_user = await db.get_user_by_username(mention)
            if mentioned_user and mentioned_user["id"] != current_user["id"]:
                notification_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": mentioned_user["id"],
                    "type": "mention",
                    "title": "Bir cevapta etiketlendiniz",
                    "message": f"{current_user['username']} sizi bir cevapta etiketledi",
                    "related_question_id": answer_data.question_id,
                    "related_answer_id": answer_id,
                    "from_user_id": current_user["id"],
                    "from_username": current_user["username"],
                    "is_read": False,
                    "created_at": datetime.utcnow().isoformat()
                }
                await db.create_notification(notification_data)
        
        return created_answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions/{question_id}/answers")
async def get_question_answers(question_id: str):
    """Get all answers for a question"""
    answers = await db.get_answers_by_question(question_id)
    return answers

@app.put("/api/answers/{answer_id}")
async def update_answer(
    answer_id: str,
    answer_update: AnswerUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an answer"""
    answer = await db.get_answer_by_id(answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Cevap bulunamadı")
    
    # Check ownership
    if answer["author_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Bu cevabı düzenleme yetkiniz yok")
    
    # Check for profanity
    content_has_profanity, found_word = contains_profanity(answer_update.content)
    if content_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"İçerik uygunsuz kelime içeriyor: '{found_word}'"
        )
    
    success = await db.update_answer(answer_id, {"content": answer_update.content})
    if not success:
        raise HTTPException(status_code=500, detail="Cevap güncellenemedi")
    
    updated_answer = await db.get_answer_by_id(answer_id)
    return updated_answer

@app.delete("/api/answers/{answer_id}")
async def delete_answer(
    answer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an answer"""
    answer = await db.get_answer_by_id(answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Cevap bulunamadı")
    
    # Check ownership
    if answer["author_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Bu cevabı silme yetkiniz yok")
    
    success = await db.delete_answer(answer_id)
    if not success:
        raise HTTPException(status_code=500, detail="Cevap silinemedi")
    
    return {"message": "Cevap başarıyla silindi"}

# =========================================
# Notification Endpoints
# =========================================

@app.get("/api/notifications")
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """Get user's notifications"""
    notifications = await db.get_user_notifications(current_user["id"], limit)
    return notifications

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark notification as read"""
    success = await db.mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=500, detail="Bildirim güncellenemedi")
    
    return {"message": "Bildirim okundu olarak işaretlendi"}

# =========================================
# Like Endpoints
# =========================================

@app.post("/api/questions/{question_id}/like")
async def toggle_question_like(
    question_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Toggle like on a question"""
    liked = await db.toggle_question_like(question_id, current_user["id"])
    return {"liked": liked}

# =========================================
# Leaderboard Endpoint
# =========================================

@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = 7):
    """Get top contributors leaderboard"""
    leaderboard = await db.get_leaderboard(limit)
    return leaderboard

# =========================================
# User Profile Endpoint
# =========================================

@app.get("/api/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Get user profile with stats"""
    profile = await db.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    return profile

# =========================================
# Static Data Endpoints
# =========================================

@app.get("/api/categories")
async def get_categories():
    """Get all categories"""
    categories = {
        "Mühendislik Fakültesi": [
            "Bilgisayar Mühendisliği", "Makine Mühendisliği", "Elektrik Mühendisliği",
            "İnşaat Mühendisliği", "Endüstri Mühendisliği", "Kimya Mühendisliği",
            "Çevre Mühendisliği", "Jeoloji Mühendisliği"
        ],
        "Tıp Fakültesi": [
            "Tıp", "Hemşirelik", "Odyoloji", "Fizyoterapi"
        ],
        "Hukuk Fakültesi": [
            "Hukuk"
        ],
        "İktisadi ve İdari Bilimler Fakültesi": [
            "İşletme", "İktisat", "Maliye", "Kamu Yönetimi", "Uluslararası İlişkiler"
        ],
        "Fen Edebiyat Fakültesi": [
            "Matematik", "Fizik", "Kimya", "Biyoloji", "Tarih", "Coğrafya", "Türk Dili ve Edebiyatı"
        ],
        "Eğitim Fakültesi": [
            "İlköğretim Öğretmenliği", "Okul Öncesi Öğretmenliği", "PDR", "Rehberlik"
        ],
        "Mimarlık Fakültesi": [
            "Mimarlık", "İç Mimarlık", "Şehir ve Bölge Planlama"
        ],
        "İletişim Fakültesi": [
            "Gazetecilik", "Halkla İlişkiler", "Radyo TV Sinema"
        ],
        "Dersler": [
            "Matematik I", "Matematik II", "Fizik I", "Fizik II", "Kimya I", "Kimya II",
            "Diferansiyel Denklemler", "Lineer Cebir", "Olasılık ve İstatistik",
            "Programlama I", "Programlama II", "Veri Yapıları", "Algoritmalar",
            "Veritabanı Sistemleri", "İşletim Sistemleri", "Bilgisayar Ağları",
            "Yapay Zeka", "Makine Öğrenmesi", "Web Programlama",
            "Mobil Programlama", "Yazılım Mühendisliği", "Yazılım Testi",
            "Bilgisayar Grafiği", "Gömülü Sistemler"
        ]
    }
    return categories

@app.get("/api/universities")
async def get_universities():
    """Get all universities"""
    universities = [
        # Istanbul Universities
        "Boğaziçi Üniversitesi", "İstanbul Teknik Üniversitesi", "İstanbul Üniversitesi",
        "Marmara Üniversitesi", "Yıldız Teknik Üniversitesi", "Galatasaray Üniversitesi",
        "Koç Üniversitesi", "Sabancı Üniversitesi", "Bahçeşehir Üniversitesi",
        
        # Ankara Universities
        "Hacettepe Üniversitesi", "Ankara Üniversitesi", "Orta Doğu Teknik Üniversitesi (ODTÜ)",
        "Gazi Üniversitesi", "Bilkent Üniversitesi", "TOBB Ekonomi ve Teknoloji Üniversitesi",
        
        # Izmir Universities
        "Ege Üniversitesi", "Dokuz Eylül Üniversitesi", "İzmir Yüksek Teknoloji Enstitüsü",
        
        # Other Major Cities
        "Çukurova Üniversitesi", "Akdeniz Üniversitesi", "Anadolu Üniversitesi",
        "Atatürk Üniversitesi", "Erciyes Üniversitesi", "Karadeniz Teknik Üniversitesi",
        "Selçuk Üniversitesi", "Ondokuz Mayıs Üniversitesi", "Uludağ Üniversitesi"
    ]
    return {"universities": sorted(universities)}

@app.get("/api/faculties")
async def get_faculties():
    """Get all faculties"""
    faculties = [
        "Mühendislik Fakültesi", "Tıp Fakültesi", "Eğitim Fakültesi",
        "İktisadi ve İdari Bilimler Fakültesi", "Hukuk Fakültesi",
        "Fen Edebiyat Fakültesi", "Mimarlık Fakültesi", "Güzel Sanatlar Fakültesi",
        "İletişim Fakültesi", "Spor Bilimleri Fakültesi", "Ziraat Fakültesi",
        "Veteriner Fakültesi", "Diş Hekimliği Fakültesi", "Eczacılık Fakültesi",
        "Sağlık Bilimleri Fakültesi", "Meslek Yüksekokulu"
    ]
    return {"faculties": sorted(faculties)}

# =========================================
# File Upload Endpoints
# =========================================

@app.post("/api/upload/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload user avatar"""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Sadece resim dosyaları yükleyebilirsiniz"
        )
    
    # Validate file size (5MB max)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Dosya boyutu 5MB'dan küçük olmalıdır"
        )
    
    # Upload to Supabase Storage
    result = await storage.upload_avatar(
        current_user["id"],
        file_content,
        file.filename,
        file.content_type
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya yüklenemedi: {result.get('error')}"
        )
    
    return {
        "message": "Avatar başarıyla yüklendi",
        "url": result["public_url"]
    }

@app.post("/api/upload/question-attachment")
async def upload_question_attachment(
    question_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload question attachment"""
    # Validate file size (20MB max)
    file_content = await file.read()
    if len(file_content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Dosya boyutu 20MB'dan küçük olmalıdır"
        )
    
    # Upload to Supabase Storage
    result = await storage.upload_question_attachment(
        current_user["id"],
        question_id,
        file_content,
        file.filename,
        file.content_type or "application/octet-stream"
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya yüklenemedi: {result.get('error')}"
        )
    
    # Save to file_uploads table
    file_id = str(uuid.uuid4())
    file_upload_data = {
        "id": file_id,
        "filename": file.filename,
        "original_filename": file.filename,
        "file_path": result["file_path"],
        "file_type": file.content_type or "application/octet-stream",
        "file_size": len(file_content),
        "uploaded_by": current_user["id"],
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    try:
        supabase_admin.table("file_uploads").insert(file_upload_data).execute()
        
        # Link to question
        supabase_admin.table("question_attachments").insert({
            "question_id": question_id,
            "file_id": file_id
        }).execute()
    except Exception as e:
        print(f"Error saving file metadata: {str(e)}")
    
    return {
        "message": "Dosya başarıyla yüklendi",
        "file_id": file_id,
        "url": result["signed_url"]
    }

@app.post("/api/upload/answer-attachment")
async def upload_answer_attachment(
    answer_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload answer attachment"""
    # Validate file size (20MB max)
    file_content = await file.read()
    if len(file_content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Dosya boyutu 20MB'dan küçük olmalıdır"
        )
    
    # Upload to Supabase Storage
    result = await storage.upload_answer_attachment(
        current_user["id"],
        answer_id,
        file_content,
        file.filename,
        file.content_type or "application/octet-stream"
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya yüklenemedi: {result.get('error')}"
        )
    
    # Save to file_uploads table
    file_id = str(uuid.uuid4())
    file_upload_data = {
        "id": file_id,
        "filename": file.filename,
        "original_filename": file.filename,
        "file_path": result["file_path"],
        "file_type": file.content_type or "application/octet-stream",
        "file_size": len(file_content),
        "uploaded_by": current_user["id"],
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    try:
        supabase_admin.table("file_uploads").insert(file_upload_data).execute()
        
        # Link to answer
        supabase_admin.table("answer_attachments").insert({
            "answer_id": answer_id,
            "file_id": file_id
        }).execute()
    except Exception as e:
        print(f"Error saving file metadata: {str(e)}")
    
    return {
        "message": "Dosya başarıyla yüklendi",
        "file_id": file_id,
        "url": result["signed_url"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
