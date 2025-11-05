from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import jwt
import os
import uuid
import re
import json
import aiomysql
import asyncio
from contextlib import asynccontextmanager

# Environment
from dotenv import load_dotenv
load_dotenv()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database connection (direct connection)

@asynccontextmanager
async def get_db_connection():
    # Direct connection (bypass pool issues)
    connection = await aiomysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        db=os.environ.get("DB_NAME", "unisoruyor"),
        charset='utf8mb4',
        autocommit=True
    )
    try:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            yield cursor
    finally:
        connection.close()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    university: str
    faculty: str
    department: str
    password_hash: str
    is_admin: bool = False  # Admin role
    is_suspended: bool = False  # Suspension status
    suspend_until: Optional[datetime] = None  # Suspension end date
    suspend_reason: Optional[str] = None  # Suspension reason
    is_muted: bool = False  # Mute status
    mute_until: Optional[datetime] = None  # Mute end date
    last_question_at: Optional[datetime] = None
    last_answer_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    university: str
    faculty: str
    department: str
    isYKSStudent: bool = False

class UserLogin(BaseModel):
    email_or_username: str  # Can be either email or username
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    university: str
    faculty: str
    department: str
    is_admin: bool = False
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class FileUpload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    author_id: str
    author_username: str
    author_university: str
    author_faculty: str
    author_department: str
    category: str
    attachments: List[str] = []  # File IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    view_count: int = 0
    answer_count: int = 0
    like_count: int = 0
    liked_by: List[str] = []  # User IDs who liked this question

class QuestionCreate(BaseModel):
    title: str
    content: str
    category: str

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Who receives the notification
    type: str  # "answer", "reply", "mention"
    title: str
    message: str
    related_question_id: Optional[str] = None
    related_answer_id: Optional[str] = None
    from_user_id: str  # Who triggered the notification
    from_username: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Answer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    content: str
    author_id: str
    author_username: str
    mentioned_users: List[str] = []  # Mentioned usernames
    attachments: List[str] = []  # File IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_accepted: bool = False
    parent_answer_id: Optional[str] = None  # For reply functionality
    reply_count: int = 0

class AnswerCreate(BaseModel):
    content: str

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str  # Question or Answer ID
    parent_type: str  # "question" or "answer"
    content: str
    author_id: str
    author_username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommentCreate(BaseModel):
    content: str

class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_count: int
    has_prev: bool
    has_next: bool

# JWT utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT *, is_suspended, suspend_until, suspend_reason 
            FROM users WHERE id = %s
        """, (user_id,))
        user_data = await cursor.fetchone()
        
        if user_data is None:
            raise credentials_exception
        
        # Check if user is suspended
        if user_data.get('is_suspended') and user_data.get('suspend_until'):
            suspend_until = user_data['suspend_until']
            # If suspend_until is still in the future, user is suspended
            if suspend_until > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=403,
                    detail=f"Hesabınız askıya alınmış. Askı süresi: {suspend_until.strftime('%d.%m.%Y %H:%M')} - Sebep: {user_data.get('suspend_reason', 'Belirtilmedi')}"
                )
            else:
                # Suspension expired, remove it
                await cursor.execute("""
                    UPDATE users 
                    SET is_suspended = FALSE, suspend_until = NULL, suspend_reason = NULL 
                    WHERE id = %s
                """, (user_id,))
                user_data['is_suspended'] = False
                user_data['suspend_until'] = None
                user_data['suspend_reason'] = None
        
        # Check if user is muted (for content creation endpoints)
        if user_data.get('is_muted') and user_data.get('mute_until'):
            mute_until = user_data['mute_until']
            if mute_until > datetime.now(timezone.utc):
                # User is muted, but we only restrict content creation, not general access
                user_data['is_currently_muted'] = True
            else:
                # Mute expired, remove it
                await cursor.execute("""
                    UPDATE users 
                    SET is_muted = FALSE, mute_until = NULL 
                    WHERE id = %s
                """, (user_id,))
                user_data['is_muted'] = False
                user_data['mute_until'] = None
                user_data['is_currently_muted'] = False
        else:
            user_data['is_currently_muted'] = False
        
        return User(**user_data)

def check_rate_limit(user: User) -> tuple[bool, int]:
    """
    Check if user can perform an action based on rate limiting.
    Returns (can_perform_action, seconds_remaining)
    """
    if user.is_admin:
        return True, 0
    
    now = datetime.now(timezone.utc)
    rate_limit_minutes = 2
    
    # Get the most recent activity time
    recent_activity = None
    if user.last_question_at and user.last_answer_at:
        recent_activity = max(user.last_question_at, user.last_answer_at)
    elif user.last_question_at:
        recent_activity = user.last_question_at
    elif user.last_answer_at:
        recent_activity = user.last_answer_at
    
    if recent_activity is None:
        return True, 0
    
    # Ensure recent_activity is timezone-aware
    if recent_activity.tzinfo is None:
        recent_activity = recent_activity.replace(tzinfo=timezone.utc)
    
    # Calculate time difference
    time_diff = now - recent_activity
    required_wait = timedelta(minutes=rate_limit_minutes)
    
    if time_diff >= required_wait:
        return True, 0
    else:
        remaining_seconds = int((required_wait - time_diff).total_seconds())
        return False, remaining_seconds

def format_time_remaining(seconds: int) -> str:
    """Format remaining time in Turkish"""
    if seconds <= 0:
        return "0 saniye"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes > 0 and remaining_seconds > 0:
        return f"{minutes} dakika {remaining_seconds} saniye"
    elif minutes > 0:
        return f"{minutes} dakika"
    else:
        return f"{remaining_seconds} saniye"

async def create_notification(user_id: str, notification_type: str, title: str, message: str, 
                            from_user_id: str, from_username: str, 
                            related_question_id: str = None, related_answer_id: str = None):
    """Create a new notification"""
    notification_id = str(uuid.uuid4())
    
    async with get_db_connection() as cursor:
        await cursor.execute("""
            INSERT INTO notifications 
            (id, user_id, type, title, message, related_question_id, related_answer_id, from_user_id, from_username)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (notification_id, user_id, notification_type, title, message, related_question_id, related_answer_id, from_user_id, from_username))

def extract_mentions(content: str) -> List[str]:
    """Extract @username mentions from content"""
    import re
    mentions = re.findall(r'@(\w+)', content)
    return list(set(mentions))  # Remove duplicates

# Initialize FastAPI
app = FastAPI(
    title="UniSoruyor.com API",
    description="Türkiye'nin en büyük üniversite öğrenci topluluğu",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Profanity filter for Turkish and English words
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
    'sıkis', 'sıkiş', 'sıkismek',
    
    # English profanity  
    'fuck', 'fucking', 'fucker', 'fucked', 'motherfucker', 'sonofabitch', 'bitch', 'bitches',
    'cunt', 'pussy', 'dick', 'dickhead', 'cock', 'asshole', 'butthole', 'jerkoff', 'whore', 'slut', 'hoe',
    'bastard', 'bastardly', 'prick', 'twat', 'wanker', 'retarded', 'retard', 'dumbass', 'idiot', 'moron',
    'stupid', 'loser', 'jerk', 'suckmydick', 'blowjob', 'handjob',
    
    # Racial slurs
    'nigger', 'negro', 'chink', 'gook', 'spic', 'wetback', 'paki', 'kike', 'jew-hater',
    'islamophobe', 'towelhead', 'sandnigger', 'terrorist', 'nazi', 'hitler lover', 'white trash',
    'redneck', 'cracker', 'monkey', 'ape', 'gypsy', 'fag', 'faggot',
    
    # Sexual content
    'porn', 'porno', 'sex', 'seks', 'xxx', 'milf', 'teen', 'hentai', 'incest', 'rape', 'gangbang',
    'fetish', 'bdsm', 'anal', 'deepthroat', 'tits', 'boobs', 'dickpic', 'nude', 'nudes',
    'escort', 'fahişe', 'jigolo', 'vajina', 'penis', 'göt deliği', 'sikmek', 'amcık', 'çük',
    'çükünü', 'taşşak', 'taşak', 'yumurtalık', 'sperm', 'boşalmak', 'orgy', 'swinger',
    
    # Drug references
    'eroin', 'heroin', 'kokain', 'cocaine', 'meth', 'metamfetamin', 'ecstasy', 'ex', 'ekstazi',
    'lsd', 'asit', 'weed', 'marihuana', 'marijuana', 'cannabis', 'esrar', 'ot', 'joint',
    'bong', 'uyuşturucu', 'hap', 'crack', 'crystal'
]

# Advanced regex patterns for bypassing attempts
PROFANITY_PATTERNS = [
    (r'\b(a[\W_]*m[\W_]*k)\b', 'amk'),
    (r'(a[\W_]*n[\W_]*a[\W_]*n[\W_]*ı[\W_]*s[\W_]*k[\W_]*m)', 'ananıskm'),
    (r'(o[\W_]*ç)', 'oç'),
    (r'(o[\W_]*r[\W_]*o[\W_]*s[\W_]*p[\W_]*u)', 'orospu'),
    (r'(o[\W_]*r[\W_]*o[\W_]*s[\W_]*p[\W_]*u[\W_]*c[\W_]*o[\W_]*[ğg][\W_]*u)', 'orospuçocuğu'),
    (r'(o[\W_]*r[\W_]*o[\W_]*s[\W_]*p[\W_]*u[\W_]*c[\W_]*o[\W_]*q[\W_]*u)', 'orospucoqu'),
    (r'(p[\W_]*[ıi][\W_]*ç)', 'piç'),
    (r'(g[\W_]*a[\W_]*v[\W_]*a[\W_]*t)', 'gavat'),
    (r'(g[\W_]*a[\W_]*v[\W_]*u[\W_]*r)', 'gavur'),
    (r'(k[\W_]*a[\W_]*h[\W_]*p[\W_]*e)', 'kahpe'),
    (r'(p[\W_]*e[\W_]*z[\W_]*e[\W_]*v[\W_]*e[\W_]*n[\W_]*k)', 'pezevenk'),
    (r'([ıi][\W_]*b[\W_]*n[\W_]*e)', 'ibne'),
    (r'([ıi][\W_]*b[\W_]*n[\W_]*e[\W_]*s[\W_]*[ıi])', 'ıbnesi'),
    (r'([ıi][\W_]*b[\W_]*n[\W_]*e[\W_]*l[\W_]*[ıi][\W_]*k)', 'ibnelik'),
    (r'(y[\W_]*a[\W_]*r[\W_]*r[\W_]*a[\W_]*[kgq])', 'yarrak'),
    (r'(y[\W_]*a[\W_]*r[\W_]*r[\W_]*a[\W_]*[gğ][\W_]*[ıi][\W_]*[mnş])', 'yarrağım'),
    (r'(s[\W_]*[ıi][\W_]*k)', 'sik'),
    (r'(s[\W_]*[ıi][\W_]*k[\W_]*e[\W_]*r)', 'siker'),
    (r'(s[\W_]*[ıi][\W_]*k[\W_]*t[\W_]*[ıi][\W_]*r)', 'siktir'),
    (r'(s[\W_]*[ıi][\W_]*ç)', 'sıç'),
    (r'(g[\W_]*ö[\W_]*t)', 'göt'),
    (r'(ş[\W_]*e[\W_]*r[\W_]*e[\W_]*f[\W_]*s[\W_]*[ıi][\W_]*z)', 'şerefsiz'),
    (r'(n[\W_]*a[\W_]*m[\W_]*u[\W_]*s[\W_]*s[\W_]*u[\W_]*z)', 'namussuz'),
    (r'(g[\W_]*e[\W_]*r[\W_]*[ıi][\W_]*z[\W_]*e[\W_]*k[\W_]*a[\W_]*l[\W_]*[ıi])', 'gerizekalı'),
    (r'(h[\W_]*a[\W_]*y[\W_]*s[\W_]*[ıi][\W_]*y[\W_]*e[\W_]*t)', 'haysıyet'),
]

def contains_profanity(text: str) -> tuple[bool, str]:
    """Check if text contains profanity and return the found word"""
    text_lower = text.lower()
    
    # Check direct word matches
    for word in PROFANITY_WORDS:
        if word.lower() in text_lower:
            return True, word
    
    # Check regex patterns for bypassing attempts
    for pattern, word in PROFANITY_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True, word
    
    return False, ""

def filter_profanity(text: str) -> str:
    """Replace profanity with asterisks"""
    filtered_text = text
    
    # Replace direct words
    for word in PROFANITY_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        filtered_text = pattern.sub('*' * len(word), filtered_text)
    
    # Replace regex patterns
    for pattern, _ in PROFANITY_PATTERNS:
        filtered_text = re.sub(pattern, lambda m: '*' * len(m.group()), filtered_text, flags=re.IGNORECASE)
    
    return filtered_text

api_router = APIRouter(prefix="/api")

# Categories data
@api_router.get("/categories")
async def get_categories():
    categories = {
        # Fakülteler ve Bölümler
        "Mühendislik Fakültesi": [
            "Bilgisayar Mühendisliği", "Makine Mühendisliği", "Elektrik Mühendisliği",
            "İnşaat Mühendisliği", "Endüstri Mühendisliği", "Harita Mühendisliği",
            "Jeoloji Mühendisliği", "Maden Mühendisliği", "Metalurji Mühendisliği",
            "Petrol Mühendisliği", "Tekstil Mühendisliği", "Gıda Mühendisliği",
            "Çevre Mühendisliği", "Biyomedikal Mühendisliği", "Malzeme Mühendisliği"
        ],
        "Tıp Fakültesi": [
            "Tıp", "Diş Hekimliği", "Eczacılık", "Veteriner Hekim",
            "Hemşirelik", "Fizyoterapi", "Beslenme ve Diyetetik",
            "Sağlık Yönetimi", "Tıbbi Sekreterlik"
        ],
        "Eğitim Fakültesi": [
            "Matematik Öğretmenliği", "Fen Bilgisi Öğretmenliği", "Sınıf Öğretmenliği",
            "İngilizce Öğretmenliği", "Türkçe Öğretmenliği", "Tarih Öğretmenliği",
            "Coğrafya Öğretmenliği", "Biyoloji Öğretmenliği", "Kimya Öğretmenliği",
            "Fizik Öğretmenliği", "Okul Öncesi Öğretmenliği", "Özel Eğitim Öğretmenliği"
        ],
        "İktisadi ve İdari Bilimler Fakültesi": [
            "İşletme", "İktisat", "Kamu Yönetimi", "Siyaset Bilimi",
            "Uluslararası İlişkiler", "Maliye", "Çalışma Ekonomisi",
            "Econometrics", "İnsan Kaynakları Yönetimi"
        ],
        "Hukuk Fakültesi": [
            "Hukuk"
        ],
        "Fen Edebiyat Fakültesi": [
            "Matematik", "Fizik", "Kimya", "Biyoloji", "Psikoloji",
            "Sosyoloji", "Türk Dili ve Edebiyatı", "Tarih", "Coğrafya",
            "Felsefe", "Arkeoloji", "Sanat Tarihi"
        ],
        "Mimarlık Fakültesi": [
            "Mimarlık", "Şehir ve Bölge Planlama", "Peyzaj Mimarlığı",
            "İç Mimarlık"
        ],
        "Güzel Sanatlar Fakültesi": [
            "Resim", "Heykel", "Grafik", "Müzik", "Sahne Sanatları",
            "Sinema ve Televizyon", "Fotoğraf"
        ],
        "İletişim Fakültesi": [
            "Gazetecilik", "Halkla İlişkiler", "Reklamcılık",
            "Radyo Televizyon ve Sinema"
        ],
        "Spor Bilimleri Fakültesi": [
            "Beden Eğitimi ve Spor Öğretmenliği", "Antrenörlük",
            "Spor Yöneticiliği", "Rekreasyon"
        ],
        "Ziraat Fakültesi": [
            "Ziraat Mühendisliği", "Peyzaj Mimarlığı", "Su Ürünleri Mühendisliği",
            "Orman Mühendisliği", "Gıda Mühendisliği"
        ],

        # KYK Yurtları (Büyük Şehirler + Diğer İller)
        "KYK Yurtları": [
            "İstanbul", "Ankara", "İzmir", "Bursa", "Eskişehir", "Diğer İller"
        ],

        # Burslar
        "Burslar": [
            "Devlet Bursları", "Özel Burslar", "Başarı Bursları", "İhtiyaç Bursları"
        ],

        # YKS (Üniversite Sınavı)
        "YKS": [
            "TYT (Temel Yeterlilik Testi)", "AYT (Alan Yeterlilik Testi)",
            "YDT (Yabancı Dil Testi)", "MSÜ (Askeri Öğrenci Seçme)",
            "DGS (Dikey Geçiş Sınavı)", "ALES (Akademik Personel ve Lisansüstü Eğitimi Giriş Sınavı)",
            "KPSS (Kamu Personeli Seçme Sınavı)", "YÖKDİL (Yabancı Dil Bilgisi Seviye Tespit Sınavı)",
            "Sınav Stratejileri", "Kaynak Önerileri", "Deneme Sınavları",
            "Puan Hesaplamaları", "Tercih Stratejileri", "Üniversite Tanıtımları",
            "Bölüm Analizleri", "Başarı Hikayeleri"
        ],

        # Zor Üniversite Dersleri
        "Dersler": [
            "Matematik (Kalkülüs)", "Diferansiyel Denklemler", "Lineer Cebir",
            "Genel Fizik", "Termodinamik", "Elektromanyetik",
            "Organik Kimya", "Fiziksel Kimya", "Analitik Kimya",
            "Anatomi", "Fizyoloji", "Biyokimya",
            "Algoritma ve Programlama", "Veri Yapıları", "Elektronik",
            "Mekanik", "Malzeme Bilimi", "İstatistik",
            "Mikroekonomi", "Makroekonomi", "Mali Muhasebe",
            "Hukuk Dersleri", "Anayasa Hukuku", "Medeni Hukuk"
        ],

        # Diğer
        "Diğer": [
            "Sosyal Aktiviteler", "Barınma", "Beslenme", "Genel Sorular"
        ]
    }
    return {"categories": categories}

# Universities endpoint
@api_router.get("/universities")
async def get_universities():
    universities = [
        # İstanbul (Devlet)
        "Boğaziçi Üniversitesi", "Galatasaray Üniversitesi", "İstanbul Medeniyet Üniversitesi",
        "İstanbul Teknik Üniversitesi", "İstanbul Üniversitesi", "İstanbul Üniversitesi-Cerrahpaşa",
        "Marmara Üniversitesi", "Milli Savunma Üniversitesi", "Mimar Sinan Güzel Sanatlar Üniversitesi",
        "Türk-Alman Üniversitesi", "Türk-Japon Bilim ve Teknoloji Üniversitesi", 
        "Sağlık Bilimleri Üniversitesi", "Yıldız Teknik Üniversitesi",
        
        # İstanbul (Vakıf)
        "Acıbadem Üniversitesi", "Altınbaş Üniversitesi", "Bahçeşehir Üniversitesi", 
        "Beykoz Üniversitesi", "Bezmialem Vakıf Üniversitesi", "Biruni Üniversitesi",
        "Demiroğlu Bilim Üniversitesi", "Doğuş Üniversitesi", "Fatih Sultan Mehmet Üniversitesi",
        "Fenerbahçe Üniversitesi", "Haliç Üniversitesi", "Işık Üniversitesi",
        "İbn Haldun Üniversitesi", "İstanbul 29 Mayıs Üniversitesi", "İstanbul Arel Üniversitesi",
        "İstanbul Atlas Üniversitesi", "İstanbul Aydın Üniversitesi", "İstanbul Beykent Üniversitesi",
        "İstanbul Bilgi Üniversitesi", "İstanbul Esenyurt Üniversitesi", "İstanbul Galata Üniversitesi",
        "İstanbul Gedik Üniversitesi", "İstanbul Gelişim Üniversitesi", "İstanbul Kent Üniversitesi",
        "İstanbul Kültür Üniversitesi", "İstanbul Medipol Üniversitesi", "İstanbul Nişantaşı Üniversitesi",
        "İstanbul Okan Üniversitesi", "İstanbul Rumeli Üniversitesi", "İstanbul Sabahattin Zaim Üniversitesi",
        "İstanbul Sağlık ve Teknoloji Üniversitesi", "İstanbul Ticaret Üniversitesi", 
        "İstanbul Topkapı Üniversitesi", "İstanbul Yeni Yüzyıl Üniversitesi", "İstinye Üniversitesi",
        "Kadir Has Üniversitesi", "Koç Üniversitesi", "Maltepe Üniversitesi", "MEF Üniversitesi",
        "Özyeğin Üniversitesi", "Piri Reis Üniversitesi", "Sabancı Üniversitesi", 
        "Üsküdar Üniversitesi", "Yeditepe Üniversitesi",
        
        # Ankara (Devlet)
        "Jandarma ve Sahil Güvenlik Akademisi", "Ankara Üniversitesi", 
        "Ankara Müzik ve Güzel Sanatlar Üniversitesi", "Ankara Hacı Bayram Veli Üniversitesi",
        "Ankara Sosyal Bilimler Üniversitesi", "Gazi Üniversitesi", "Hacettepe Üniversitesi",
        "Orta Doğu Teknik Üniversitesi", "Ankara Yıldırım Beyazıt Üniversitesi", "Polis Akademisi",
        
        # Ankara (Vakıf)
        "Ankara Bilim Üniversitesi", "Ankara Medipol Üniversitesi", "Atılım Üniversitesi",
        "Başkent Üniversitesi", "Çankaya Üniversitesi", "İhsan Doğramacı Bilkent Üniversitesi",
        "Lokman Hekim Üniversitesi", "Ostim Teknik Üniversitesi", "TED Üniversitesi",
        "TOBB Ekonomi ve Teknoloji Üniversitesi", "Ufuk Üniversitesi", 
        "Türk Hava Kurumu Üniversitesi", "Yüksek İhtisas Üniversitesi",
        
        # İzmir (Devlet)
        "Dokuz Eylül Üniversitesi", "Ege Üniversitesi", "İzmir Yüksek Teknoloji Enstitüsü",
        "İzmir Kâtip Çelebi Üniversitesi", "İzmir Bakırçay Üniversitesi", "İzmir Demokrasi Üniversitesi",
        
        # İzmir (Vakıf)
        "İzmir Ekonomi Üniversitesi", "İzmir Tınaztepe Üniversitesi", "Yaşar Üniversitesi",
        
        # Diğer Şehirler (Devlet)
        "Adana Alparslan Türkeş Bilim ve Teknoloji Üniversitesi", "Çukurova Üniversitesi",
        "Adıyaman Üniversitesi", "Afyon Kocatepe Üniversitesi", "Afyonkarahisar Sağlık Bilimleri Üniversitesi",
        "Ağrı İbrahim Çeçen Üniversitesi", "Aksaray Üniversitesi", "Amasya Üniversitesi",
        "Akdeniz Üniversitesi", "Alanya Alaaddin Keykubat Üniversitesi", "Ardahan Üniversitesi",
        "Artvin Çoruh Üniversitesi", "Aydın Adnan Menderes Üniversitesi", "Balıkesir Üniversitesi",
        "Bandırma Onyedi Eylül Üniversitesi", "Bartın Üniversitesi", "Batman Üniversitesi",
        "Bayburt Üniversitesi", "Bilecik Şeyh Edebali Üniversitesi", "Bingöl Üniversitesi",
        "Bitlis Eren Üniversitesi", "Bolu Abant İzzet Baysal Üniversitesi", "Burdur Mehmet Akif Ersoy Üniversitesi",
        "Bursa Teknik Üniversitesi", "Bursa Uludağ Üniversitesi", "Çanakkale Onsekiz Mart Üniversitesi",
        "Çankırı Karatekin Üniversitesi", "Hitit Üniversitesi", "Pamukkale Üniversitesi",
        "Dicle Üniversitesi", "Düzce Üniversitesi", "Trakya Üniversitesi", "Fırat Üniversitesi",
        "Erzincan Binali Yıldırım Üniversitesi", "Atatürk Üniversitesi", "Erzurum Teknik Üniversitesi",
        "Anadolu Üniversitesi", "Eskişehir Osmangazi Üniversitesi", "Eskişehir Teknik Üniversitesi",
        "Gaziantep Üniversitesi", "Gaziantep İslam Bilim ve Teknoloji Üniversitesi", "Giresun Üniversitesi",
        "Gümüşhane Üniversitesi", "Hakkari Üniversitesi", "İskenderun Teknik Üniversitesi",
        "Hatay Mustafa Kemal Üniversitesi", "Iğdır Üniversitesi", "Süleyman Demirel Üniversitesi",
        "Isparta Uygulamalı Bilimler Üniversitesi", "Kahramanmaraş Sütçü İmam Üniversitesi",
        "Kahramanmaraş İstiklal Üniversitesi", "Karabük Üniversitesi", "Karamanoğlu Mehmetbey Üniversitesi",
        "Kafkas Üniversitesi", "Kastamonu Üniversitesi", "Abdullah Gül Üniversitesi",
        "Erciyes Üniversitesi", "Kayseri Üniversitesi", "Kırıkkale Üniversitesi", "Kırklareli Üniversitesi",
        "Kırşehir Ahi Evran Üniversitesi", "Kilis 7 Aralık Üniversitesi", "Gebze Teknik Üniversitesi",
        "Kocaeli Üniversitesi", "Konya Teknik Üniversitesi", "Necmettin Erbakan Üniversitesi",
        "Selçuk Üniversitesi", "Kütahya Dumlupınar Üniversitesi", "Kütahya Sağlık Bilimleri Üniversitesi",
        "İnönü Üniversitesi", "Malatya Turgut Özal Üniversitesi", "Manisa Celal Bayar Üniversitesi",
        "Mardin Artuklu Üniversitesi", "Mersin Üniversitesi", "Tarsus Üniversitesi",
        "Muğla Sıtkı Koçman Üniversitesi", "Muş Alparslan Üniversitesi", "Nevşehir Hacı Bektaş Veli Üniversitesi",
        "Niğde Ömer Halisdemir Üniversitesi", "Ordu Üniversitesi", "Osmaniye Korkut Ata Üniversitesi",
        "Recep Tayyip Erdoğan Üniversitesi", "Sakarya Üniversitesi", "Sakarya Uygulamalı Bilimler Üniversitesi",
        "Ondokuz Mayıs Üniversitesi", "Samsun Üniversitesi", "Siirt Üniversitesi", "Sinop Üniversitesi",
        "Sivas Cumhuriyet Üniversitesi", "Sivas Bilim ve Teknoloji Üniversitesi", "Şırnak Üniversitesi",
        "Tekirdağ Namık Kemal Üniversitesi", "Tokat Gaziosmanpaşa Üniversitesi", "Trabzon Üniversitesi",
        "Karadeniz Teknik Üniversitesi", "Uşak Üniversitesi", "Van Yüzüncü Yıl Üniversitesi",
        "Yalova Üniversitesi", "Yozgat Bozok Üniversitesi", "Zonguldak Bülent Ecevit Üniversitesi",
        
        # Vakıf Üniversiteleri (Diğer Şehirler)
        "Alanya Üniversitesi", "Antalya Belek Üniversitesi", "Antalya Bilim Üniversitesi",
        "Hasan Kalyoncu Üniversitesi", "Sanko Üniversitesi", "Mudanya Üniversitesi",
        "Çağ Üniversitesi", "Toros Üniversitesi", "Kapadokya Üniversitesi", "Nuh Naci Yazgan Üniversitesi",
        "Kocaeli Sağlık ve Teknoloji Üniversitesi", "Konya Gıda ve Tarım Üniversitesi", 
        "KTO Karatay Üniversitesi"
    ]
    
    # Remove duplicates and sort
    universities = sorted(list(set(universities)))
    return {"universities": universities}

# Faculties endpoint
@api_router.get("/faculties")
async def get_faculties():
    faculties = [
        "Mühendislik Fakültesi",
        "Tıp Fakültesi", 
        "Eğitim Fakültesi",
        "İktisadi ve İdari Bilimler Fakültesi",
        "Hukuk Fakültesi",
        "Fen Edebiyat Fakültesi",
        "Mimarlık Fakültesi",
        "Güzel Sanatlar Fakültesi",
        "İletişim Fakültesi",
        "Spor Bilimleri Fakültesi",
        "Ziraat Fakültesi",
        "Veteriner Fakültesi",
        "Diş Hekimliği Fakültesi",
        "Eczacılık Fakültesi",
        "Sağlık Bilimleri Fakültesi",
        "Teknoloji Fakültesi",
        "Meslek Yüksekokulu",
        "İlahiyat Fakültesi",
        "Turizm Fakültesi"
    ]
    return {"faculties": sorted(faculties)}

# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check for profanity in username
    username_has_profanity, found_word = contains_profanity(user_data.username)
    if username_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"Kullanıcı adınızda uygunsuz kelime tespit edildi: '{found_word}'. Lütfen farklı bir kullanıcı adı seçin."
        )
    
    async with get_db_connection() as cursor:
        # Check if user exists
        await cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (user_data.email, user_data.username))
        existing_user = await cursor.fetchone()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Mail adresi veya kullanıcı adı zaten kullanılıyor")
        
        # Hash password and create user
        password_hash = pwd_context.hash(user_data.password)
        user_id = str(uuid.uuid4())
        
        # Set university info based on YKS student status
        if user_data.isYKSStudent:
            university = "YKS Öğrencisi"
            faculty = "YKS Öğrencisi"  
            department = "YKS Öğrencisi"
        else:
            university = user_data.university
            faculty = user_data.faculty
            department = user_data.department
        
        await cursor.execute("""
            INSERT INTO users (id, username, email, university, faculty, department, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, user_data.username, user_data.email, university, 
              faculty, department, password_hash))
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        user_response = UserResponse(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            university=user_data.university,
            faculty=user_data.faculty,
            department=user_data.department,
            created_at=datetime.now(timezone.utc)
        )
        
        return {"access_token": access_token, "token_type": "bearer", "user": user_response}

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    async with get_db_connection() as cursor:
        # Check by email or username
        await cursor.execute("""
            SELECT * FROM users 
            WHERE email = %s OR username = %s
        """, (user_credentials.email_or_username, user_credentials.email_or_username))
        
        user = await cursor.fetchone()
        
        if not user or not pwd_context.verify(user_credentials.password, user['password_hash']):
            raise HTTPException(status_code=400, detail="Mail adresi/kullanıcı adı veya şifre hatalı")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user['id']}, expires_delta=access_token_expires
        )
        
        user_response = UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            university=user['university'],
            faculty=user['faculty'],
            department=user['department'],
            is_admin=bool(user.get('is_admin', False)),
            created_at=user['created_at']
        )
        
        return {"access_token": access_token, "token_type": "bearer", "user": user_response}

# Get current user endpoint
@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Question endpoints
@api_router.post("/questions", response_model=Question)
async def create_question(
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user)
):
    # Check rate limit
    can_post, seconds_remaining = check_rate_limit(current_user)
    if not can_post:
        time_remaining = format_time_remaining(seconds_remaining)
        raise HTTPException(
            status_code=429, 
            detail=f"Çok sık soru soruyorsunuz. {time_remaining} sonra tekrar deneyebilirsiniz."
        )
    
    # Check if user is muted
    if hasattr(current_user, 'is_currently_muted') and current_user.is_currently_muted:
        mute_until = current_user.mute_until.strftime('%d.%m.%Y %H:%M') if current_user.mute_until else 'bilinmiyor'
        raise HTTPException(
            status_code=403,
            detail=f"Hesabınız susturulmuş durumda. Susturma süresi: {mute_until}. Bu süre içinde soru gönderemezsiniz."
        )
    
    # Check for profanity
    title_has_profanity, found_word = contains_profanity(question_data.title)
    content_has_profanity, found_word2 = contains_profanity(question_data.content)
    
    if title_has_profanity or content_has_profanity:
        profane_word = found_word or found_word2
        raise HTTPException(
            status_code=400,
            detail=f"İçeriğinizde uygunsuz kelime tespit edildi: '{profane_word}'. Lütfen saygılı bir dil kullanın."
        )
    
    question_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    question = Question(
        id=question_id,
        title=question_data.title,
        content=question_data.content,
        author_id=current_user.id,
        author_username=current_user.username,
        author_university=current_user.university,
        author_faculty=current_user.faculty,
        author_department=current_user.department,
        category=question_data.category,
        created_at=now,
        updated_at=now
    )
    
    async with get_db_connection() as cursor:
        await cursor.execute("""
            INSERT INTO questions 
            (id, title, content, author_id, author_username, author_university, author_faculty, author_department, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (question_id, question_data.title, question_data.content, current_user.id,
              current_user.username, current_user.university, current_user.faculty,
              current_user.department, question_data.category))
        
        # Update user's last question timestamp
        await cursor.execute(
            "UPDATE users SET last_question_at = %s WHERE id = %s",
            (now, current_user.id)
        )
    
    return question

@api_router.get("/questions")
async def get_questions(page: int = 1, limit: int = 15, category: str = None):
    offset = (page - 1) * limit
    
    async with get_db_connection() as cursor:
        # Build query with optional category filter
        if category:
            count_query = "SELECT COUNT(*) as total FROM questions WHERE category LIKE %s"
            questions_query = """
                SELECT q.*, 
                       (SELECT COUNT(*) FROM question_likes ql WHERE ql.question_id = q.id) as like_count
                FROM questions q 
                WHERE category LIKE %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            await cursor.execute(count_query, (f"%{category}%",))
            total_result = await cursor.fetchone()
            total_count = total_result['total']
            
            await cursor.execute(questions_query, (f"%{category}%", limit, offset))
        else:
            count_query = "SELECT COUNT(*) as total FROM questions"
            questions_query = """
                SELECT q.*,
                       (SELECT COUNT(*) FROM question_likes ql WHERE ql.question_id = q.id) as like_count
                FROM questions q 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            await cursor.execute(count_query)
            total_result = await cursor.fetchone()
            total_count = total_result['total']
            
            await cursor.execute(questions_query, (limit, offset))
        
        questions_data = await cursor.fetchall()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_prev = page > 1
        has_next = page < total_pages
        
        pagination = PaginationInfo(
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            has_prev=has_prev,
            has_next=has_next
        )
        
        questions = []
        for q_data in questions_data:
            question = Question(**q_data)
            questions.append(question)
        
        return {
            "questions": questions,
            "pagination": pagination
        }

# Get single question by ID
@api_router.get("/questions/{question_id}")
async def get_question(question_id: str):
    async with get_db_connection() as cursor:
        # Get question details with author info and like count
        await cursor.execute("""
            SELECT q.*, 
                   u.username as author_username,
                   u.university as author_university,
                   u.faculty as author_faculty,
                   u.department as author_department,
                   (SELECT COUNT(*) FROM question_likes ql WHERE ql.question_id = q.id) as like_count,
                   (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) as answer_count
            FROM questions q
            JOIN users u ON q.author_id = u.id
            WHERE q.id = %s
        """, (question_id,))
        
        question = await cursor.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Get question likes
        await cursor.execute("""
            SELECT user_id FROM question_likes WHERE question_id = %s
        """, (question_id,))
        likes = await cursor.fetchall()
        liked_by = [like['user_id'] for like in likes]
        
        # Get attachments (currently not supported in this table structure)
        attachments = []
        
        # Increment view count
        await cursor.execute("""
            UPDATE questions SET view_count = view_count + 1 WHERE id = %s
        """, (question_id,))
        
        question_data = {
            "id": question['id'],
            "title": question['title'],
            "content": question['content'],
            "author_id": question['author_id'],
            "author_username": question['author_username'],
            "author_university": question['author_university'],
            "author_faculty": question['author_faculty'],
            "author_department": question['author_department'],
            "category": question['category'],
            "attachments": attachments or [],
            "created_at": question['created_at'],
            "updated_at": question['updated_at'],
            "view_count": question['view_count'] + 1,  # Updated count
            "answer_count": question['answer_count'],
            "like_count": question['like_count'],
            "liked_by": liked_by
        }
        
        return question_data

# Like/Unlike question endpoints
@api_router.post("/questions/{question_id}/like")
async def like_question(question_id: str, current_user: User = Depends(get_current_user)):
    async with get_db_connection() as cursor:
        # Check if question exists
        await cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = await cursor.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Check if already liked
        await cursor.execute(
            "SELECT * FROM question_likes WHERE question_id = %s AND user_id = %s",
            (question_id, current_user.id)
        )
        existing_like = await cursor.fetchone()
        
        if existing_like:
            raise HTTPException(status_code=400, detail="Bu soruyu zaten beğenmişsiniz")
        
        # Add like
        await cursor.execute(
            "INSERT INTO question_likes (question_id, user_id) VALUES (%s, %s)",
            (question_id, current_user.id)
        )
        
        # Get new like count
        await cursor.execute(
            "SELECT COUNT(*) as like_count FROM question_likes WHERE question_id = %s",
            (question_id,)
        )
        like_count = await cursor.fetchone()
        
        # NO NOTIFICATION for question likes (as requested by user)
        
        return {
            "message": "Soru beğenildi",
            "like_count": like_count['like_count'],
            "liked": True
        }

@api_router.delete("/questions/{question_id}/like")
async def unlike_question(question_id: str, current_user: User = Depends(get_current_user)):
    async with get_db_connection() as cursor:
        # Check if question exists
        await cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = await cursor.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Check if liked
        await cursor.execute(
            "SELECT * FROM question_likes WHERE question_id = %s AND user_id = %s",
            (question_id, current_user.id)
        )
        existing_like = await cursor.fetchone()
        
        if not existing_like:
            raise HTTPException(status_code=400, detail="Bu soruyu beğenmemişsiniz")
        
        # Remove like
        await cursor.execute(
            "DELETE FROM question_likes WHERE question_id = %s AND user_id = %s",
            (question_id, current_user.id)
        )
        
        # Get new like count
        await cursor.execute(
            "SELECT COUNT(*) as like_count FROM question_likes WHERE question_id = %s",
            (question_id,)
        )
        like_count = await cursor.fetchone()
        
        return {
            "message": "Soru beğenisi kaldırıldı",
            "like_count": like_count['like_count'],
            "liked": False
        }

# Simple question delete endpoint
@api_router.delete("/questions/{question_id}")
async def delete_question(question_id: str, current_user: User = Depends(get_current_user)):
    """Delete a question - simple and reliable"""
    async with get_db_connection() as cursor:
        # Get question info
        await cursor.execute("SELECT author_id FROM questions WHERE id = %s", (question_id,))
        question = await cursor.fetchone()
        
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Check permission
        if question['author_id'] != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Bu soruyu silme yetkiniz yok")
        
        # Simple delete (let foreign keys cascade)
        await cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        
        return {"success": True, "message": "Soru silindi"}



# Answer endpoints
@api_router.post("/questions/{question_id}/answers", response_model=Answer)
async def create_answer(
    question_id: str,
    answer_data: AnswerCreate,
    current_user: User = Depends(get_current_user)
):
    # Check rate limit
    can_post, seconds_remaining = check_rate_limit(current_user)
    if not can_post:
        time_remaining = format_time_remaining(seconds_remaining)
        raise HTTPException(
            status_code=429, 
            detail=f"Çok sık cevap veriyorsunuz. {time_remaining} sonra tekrar deneyebilirsiniz."
        )
    
    # Check if user is muted
    if hasattr(current_user, 'is_currently_muted') and current_user.is_currently_muted:
        mute_until = current_user.mute_until.strftime('%d.%m.%Y %H:%M') if current_user.mute_until else 'bilinmiyor'
        raise HTTPException(
            status_code=403,
            detail=f"Hesabınız susturulmuş durumda. Susturma süresi: {mute_until}. Bu süre içinde cevap gönderemezsiniz."
        )
    
    # Check for profanity  
    content_has_profanity, found_word = contains_profanity(answer_data.content)
    if content_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"Cevabınızda uygunsuz kelime tespit edildi: '{found_word}'. Lütfen saygılı bir dil kullanın."
        )
    
    async with get_db_connection() as cursor:
        # Check if question exists
        await cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = await cursor.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Extract mentions from answer content
        mentioned_users = extract_mentions(answer_data.content)
        
        answer_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Create answer
        await cursor.execute("""
            INSERT INTO answers 
            (id, question_id, content, author_id, author_username, mentioned_users)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (answer_id, question_id, answer_data.content, current_user.id,
              current_user.username, json.dumps(mentioned_users)))
        
        # Update question answer count
        await cursor.execute(
            "UPDATE questions SET answer_count = answer_count + 1 WHERE id = %s",
            (question_id,)
        )
        
        # Update user's last answer timestamp
        await cursor.execute(
            "UPDATE users SET last_answer_at = %s WHERE id = %s",
            (now, current_user.id)
        )
        
        # Create notification for question author (if not self-answering)
        if question['author_id'] != current_user.id:
            await create_notification(
                user_id=question['author_id'],
                notification_type="answer",
                title="Sorunuza yeni cevap",
                message=f"{current_user.username} sorunuza cevap verdi: \"{question['title']}\"",
                from_user_id=current_user.id,
                from_username=current_user.username,
                related_question_id=question_id,
                related_answer_id=answer_id
            )
        
        # Create notifications for mentioned users
        for mentioned_username in mentioned_users:
            await cursor.execute("SELECT id FROM users WHERE username = %s", (mentioned_username,))
            mentioned_user = await cursor.fetchone()
            if mentioned_user and mentioned_user['id'] != current_user.id:
                await create_notification(
                    user_id=mentioned_user['id'],
                    notification_type="mention",
                    title="Bir cevapta etiketlendiniz",
                    message=f"{current_user.username} sizi bir cevapta etiketledi",
                    from_user_id=current_user.id,
                    from_username=current_user.username,
                    related_question_id=question_id,
                    related_answer_id=answer_id
                )
        
        answer = Answer(
            id=answer_id,
            question_id=question_id,
            content=answer_data.content,
            author_id=current_user.id,
            author_username=current_user.username,
            mentioned_users=mentioned_users,
            created_at=now,
            updated_at=now
        )
        
        return answer

# Reply to answer endpoint
@api_router.post("/answers/{answer_id}/replies")
async def create_reply(
    answer_id: str,
    reply_data: AnswerCreate,
    current_user: User = Depends(get_current_user)
):
    # Check rate limit
    can_post, seconds_remaining = check_rate_limit(current_user)
    if not can_post:
        time_remaining = format_time_remaining(seconds_remaining)
        raise HTTPException(
            status_code=429, 
            detail=f"Çok hızlı cevap veriyorsunuz. {time_remaining} sonra tekrar deneyin."
        )
    
    # Check if user is muted
    if hasattr(current_user, 'is_currently_muted') and current_user.is_currently_muted:
        mute_until = current_user.mute_until.strftime('%d.%m.%Y %H:%M') if current_user.mute_until else 'bilinmiyor'
        raise HTTPException(
            status_code=403,
            detail=f"Hesabınız susturulmuş durumda. Susturma süresi: {mute_until}. Bu süre içinde yanıt gönderemezsiniz."
        )
    
    # Check for profanity
    content_has_profanity, found_word = contains_profanity(reply_data.content)
    if content_has_profanity:
        raise HTTPException(
            status_code=400,
            detail=f"Yanıtınızda uygunsuz kelime tespit edildi: '{found_word}'. Lütfen saygılı bir dil kullanın."
        )
    
    async with get_db_connection() as cursor:
        # Check if parent answer exists
        await cursor.execute("SELECT * FROM answers WHERE id = %s", (answer_id,))
        parent_answer = await cursor.fetchone()
        if not parent_answer:
            raise HTTPException(status_code=404, detail="Cevap bulunamadı")
        
        # Create reply
        reply_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        mentioned_users = extract_mentions(reply_data.content)
        
        await cursor.execute("""
            INSERT INTO answers (id, question_id, content, author_id, author_username, mentioned_users, parent_answer_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (reply_id, parent_answer['question_id'], reply_data.content, current_user.id, current_user.username, 
              json.dumps(mentioned_users), answer_id, now, now))
        
        # Update parent answer reply count
        await cursor.execute("""
            UPDATE answers SET reply_count = reply_count + 1 WHERE id = %s
        """, (answer_id,))
        
        # Update user's last answer time
        await cursor.execute("""
            UPDATE users SET last_answer_at = %s WHERE id = %s
        """, (now, current_user.id))
        
        # Create notification for parent answer author
        if parent_answer['author_id'] != current_user.id:
            await create_notification(
                user_id=parent_answer['author_id'],
                notification_type="reply",
                title="Cevabınıza yanıt geldi",
                message=f"{current_user.username} cevabınıza yanıt verdi",
                from_user_id=current_user.id,
                from_username=current_user.username,
                related_question_id=parent_answer['question_id'],
                related_answer_id=reply_id
            )
        
        reply = Answer(
            id=reply_id,
            question_id=parent_answer['question_id'],
            content=reply_data.content,
            author_id=current_user.id,
            author_username=current_user.username,
            mentioned_users=mentioned_users,
            parent_answer_id=answer_id,
            created_at=now,
            updated_at=now
        )
        
        return reply

# Get replies for an answer
@api_router.get("/answers/{answer_id}/replies")
async def get_replies(answer_id: str):
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT a.*, u.username as author_username,
                   u.university as author_university,
                   u.faculty as author_faculty,
                   u.department as author_department
            FROM answers a
            JOIN users u ON a.author_id = u.id
            WHERE a.parent_answer_id = %s
            ORDER BY a.created_at ASC
        """, (answer_id,))
        
        replies = await cursor.fetchall()
        return {"replies": replies or []}

# Delete answer endpoint
@api_router.delete("/answers/{answer_id}")
async def delete_answer(answer_id: str, current_user: User = Depends(get_current_user)):
    async with get_db_connection() as cursor:
        # Check if answer exists and user owns it
        await cursor.execute("SELECT * FROM answers WHERE id = %s", (answer_id,))
        answer = await cursor.fetchone()
        
        if not answer:
            raise HTTPException(status_code=404, detail="Cevap bulunamadı")
        
        if answer['author_id'] != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Bu cevabı silme yetkiniz yok")
        
        # Delete all replies to this answer first
        await cursor.execute("DELETE FROM answers WHERE parent_answer_id = %s", (answer_id,))
        
        # Delete the answer
        await cursor.execute("DELETE FROM answers WHERE id = %s", (answer_id,))
        
        # Update parent answer reply count if this was a reply
        if answer['parent_answer_id']:
            await cursor.execute("""
                UPDATE answers SET reply_count = reply_count - 1 
                WHERE id = %s AND reply_count > 0
            """, (answer['parent_answer_id'],))
        
        return {"message": "Cevap başarıyla silindi"}

# Rate limiting endpoints

@api_router.get("/questions/{question_id}/answers")
async def get_answers(question_id: str):
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT * FROM answers 
            WHERE question_id = %s 
            ORDER BY created_at ASC
        """, (question_id,))
        
        answers_data = await cursor.fetchall()
        
        answers = []
        for a_data in answers_data:
            # Parse mentioned_users JSON
            mentioned_users = json.loads(a_data['mentioned_users']) if a_data['mentioned_users'] else []
            
            answer = Answer(
                **{**a_data, 'mentioned_users': mentioned_users}
            )
            answers.append(answer)
        
        return {"answers": answers}

# Leaderboard endpoint
@api_router.get("/leaderboard")
async def get_leaderboard():
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT 
                u.username,
                u.university,
                u.faculty,
                COUNT(DISTINCT q.id) as question_count,
                COUNT(DISTINCT a.id) as answer_count,
                (COUNT(DISTINCT q.id) * 2 + COUNT(DISTINCT a.id)) as total_points
            FROM users u
            LEFT JOIN questions q ON u.id = q.author_id 
                AND q.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            LEFT JOIN answers a ON u.id = a.author_id 
                AND a.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY u.id, u.username, u.university, u.faculty
            HAVING total_points > 0
            ORDER BY total_points DESC, question_count DESC, u.username ASC
            LIMIT 7
        """)
        
        leaderboard_data = await cursor.fetchall()
        
        leaderboard = []
        for i, user_data in enumerate(leaderboard_data, 1):
            leaderboard.append({
                "rank": i,
                "username": user_data['username'],
                "university": user_data['university'],
                "faculty": user_data['faculty'],
                "question_count": user_data['question_count'],
                "answer_count": user_data['answer_count'],
                "total_points": user_data['total_points']
            })
        
        return {"leaderboard": leaderboard}

# Notifications endpoints
@api_router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT * FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (current_user.id,))
        
        notifications_data = await cursor.fetchall()
        
        notifications = []
        for n_data in notifications_data:
            notification = Notification(**n_data)
            notifications.append(notification)
        
        return {"notifications": notifications}

@api_router.get("/notifications/unread-count")
async def get_unread_notifications_count(current_user: User = Depends(get_current_user)):
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT COUNT(*) as count FROM notifications 
            WHERE user_id = %s AND is_read = FALSE
        """, (current_user.id,))
        
        result = await cursor.fetchone()
        return {"unread_count": result['count']}

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    async with get_db_connection() as cursor:
        await cursor.execute("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE id = %s AND user_id = %s
        """, (notification_id, current_user.id))
        
        return {"message": "Bildirim okundu olarak işaretlendi"}

# User Profile endpoint
@api_router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    async with get_db_connection() as cursor:
        # Get user basic info
        await cursor.execute("""
            SELECT id, username, email, university, faculty, department, created_at
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user_data = await cursor.fetchone()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Get user statistics
        await cursor.execute("""
            SELECT 
                COUNT(DISTINCT q.id) as question_count,
                COUNT(DISTINCT a.id) as answer_count,
                COALESCE(SUM(q.like_count), 0) as total_likes
            FROM users u
            LEFT JOIN questions q ON u.id = q.author_id
            LEFT JOIN answers a ON u.id = a.author_id
            WHERE u.id = %s
            GROUP BY u.id
        """, (user_id,))
        
        stats_data = await cursor.fetchone()
        
        # Get recent questions (last 5)
        await cursor.execute("""
            SELECT id, title, category, created_at, answer_count
            FROM questions 
            WHERE author_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        
        recent_questions = await cursor.fetchall()
        
        # Get recent answers (last 5)
        await cursor.execute("""
            SELECT a.id, a.content, a.created_at, q.title as question_title, q.id as question_id
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.author_id = %s 
            ORDER BY a.created_at DESC 
            LIMIT 5
        """, (user_id,))
        
        recent_answers = await cursor.fetchall()
        
        profile = {
            "user": {
                "id": user_data['id'],
                "username": user_data['username'],
                "email": user_data['email'],
                "university": user_data['university'],
                "faculty": user_data['faculty'],
                "department": user_data['department'],
                "created_at": user_data['created_at']
            },
            "stats": {
                "question_count": stats_data['question_count'] if stats_data else 0,
                "answer_count": stats_data['answer_count'] if stats_data else 0,
                "total_likes": stats_data['total_likes'] if stats_data else 0
            },
            "recent_questions": recent_questions or [],
            "recent_answers": recent_answers or []
        }
        
        return profile

# File Upload endpoint
@api_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dosya boyutu çok büyük (maksimum 10MB)")
    
    # Validate file type
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya türü")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{file_id}.{file_extension}" if file_extension else file_id
    
    # Create uploads directory if it doesn't exist
    upload_dir = "/tmp/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Dosya kaydetme hatası")
    
    # Save file info to database
    async with get_db_connection() as cursor:
        await cursor.execute("""
            INSERT INTO file_uploads (
                id, filename, original_filename, file_path, 
                file_type, file_size, uploaded_by, uploaded_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            file_id,
            unique_filename,
            file.filename,
            file_path,
            file.content_type,
            file.size,
            current_user.id,
            datetime.now(timezone.utc)
        ))
    
    return {
        "file_id": file_id,
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_type": file.content_type,
        "file_size": file.size,
        "upload_url": f"/uploads/{unique_filename}"
    }

# File serving endpoint  
@api_router.get("/uploads/{filename}")
async def serve_file(filename: str):
    file_path = f"/tmp/uploads/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    
    return FileResponse(file_path)

# Admin endpoints
@api_router.post("/admin/suspend-user/{user_id}")
async def suspend_user(
    user_id: str, 
    suspend_days: int,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        # Calculate suspend until date
        suspend_until = datetime.now(timezone.utc) + timedelta(days=suspend_days)
        
        # Update user
        await cursor.execute("""
            UPDATE users 
            SET is_suspended = TRUE, suspend_until = %s, suspend_reason = %s 
            WHERE id = %s
        """, (suspend_until, reason, user_id))
        
        # Get user info
        await cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Create notification for suspended user
        notification_id = str(uuid.uuid4())
        await cursor.execute("""
            INSERT INTO notifications (id, user_id, message, type, created_at) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            notification_id,
            user_id,
            f"Hesabınız {suspend_days} gün süreyle askıya alınmıştır. Sebep: {reason}. Askı süresi: {suspend_until.strftime('%d.%m.%Y %H:%M')}",
            "suspend",
            datetime.now(timezone.utc)
        ))
        
        return {"message": f"Kullanıcı {suspend_days} gün askıya alındı", "user": user_info['username']}

@api_router.post("/admin/unsuspend-user/{user_id}")
async def unsuspend_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        await cursor.execute("""
            UPDATE users 
            SET is_suspended = FALSE, suspend_until = NULL, suspend_reason = NULL 
            WHERE id = %s
        """, (user_id,))
        
        # Get user info
        await cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Create notification
        notification_id = str(uuid.uuid4())
        await cursor.execute("""
            INSERT INTO notifications (id, user_id, message, type, created_at) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            notification_id,
            user_id,
            "Hesabınızın askısı kaldırılmıştır. Artık normal şekilde platform kullanabilirsiniz.",
            "unsuspend",
            datetime.now(timezone.utc)
        ))
        
        return {"message": "Kullanıcının askısı kaldırıldı", "user": user_info['username']}

@api_router.delete("/admin/delete-user/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        # Get user info first
        await cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Delete user (CASCADE will handle related data)
        await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        return {"message": f"Kullanıcı {user_info['username']} silindi"}

@api_router.delete("/admin/delete-question/{question_id}")
async def admin_delete_question(question_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        # Check if question exists
        await cursor.execute("SELECT title, author_username FROM questions WHERE id = %s", (question_id,))
        question = await cursor.fetchone()
        
        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        
        # Delete question (CASCADE will handle answers, likes, etc.)
        await cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        
        return {"success": True, "message": f"Soru '{question['title']}' admin tarafından silindi"}

@api_router.delete("/admin/delete-answer/{answer_id}")
async def admin_delete_answer(answer_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        # Check if answer exists
        await cursor.execute("SELECT content, author_username FROM answers WHERE id = %s", (answer_id,))
        answer = await cursor.fetchone()
        
        if not answer:
            raise HTTPException(status_code=404, detail="Cevap bulunamadı")
        
        # Delete answer (CASCADE will handle replies)
        await cursor.execute("DELETE FROM answers WHERE id = %s", (answer_id,))
        
        return {"success": True, "message": "Cevap admin tarafından silindi"}

@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        # Only return admin users by default
        await cursor.execute("""
            SELECT 
                id, username, email, university, faculty, department,
                is_admin, is_suspended, suspend_until, suspend_reason,
                is_muted, mute_until, created_at,
                (SELECT COUNT(*) FROM questions WHERE author_id = u.id) as question_count,
                (SELECT COUNT(*) FROM answers WHERE author_id = u.id) as answer_count
            FROM users u
            WHERE is_admin = TRUE
            ORDER BY created_at DESC
        """)
        
        users = await cursor.fetchall()
        
        return {"users": users}

@api_router.get("/admin/search-users")
async def search_users(
    q: str, 
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Arama terimi en az 2 karakter olmalı")
    
    search_term = f"%{q.strip()}%"
    
    async with get_db_connection() as cursor:
        await cursor.execute("""
            SELECT 
                id, username, email, university, faculty, department,
                is_admin, is_suspended, suspend_until, suspend_reason,
                is_muted, mute_until, created_at,
                (SELECT COUNT(*) FROM questions WHERE author_id = u.id) as question_count,
                (SELECT COUNT(*) FROM answers WHERE author_id = u.id) as answer_count
            FROM users u
            WHERE (username LIKE %s OR email LIKE %s OR university LIKE %s)
            ORDER BY is_admin DESC, created_at DESC
            LIMIT 20
        """, (search_term, search_term, search_term))
        
        users = await cursor.fetchall()
        
        return {"users": users, "search_term": q}

@api_router.post("/admin/make-admin/{user_id}")
async def make_admin(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        await cursor.execute("UPDATE users SET is_admin = TRUE WHERE id = %s", (user_id,))
        
        # Get user info
        await cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        return {"message": f"{user_info['username']} admin yapıldı"}

@api_router.post("/admin/warn-user/{user_id}")
async def warn_user(
    user_id: str, 
    request: dict,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    warning_message = request.get('warning_message', '')
    if not warning_message.strip():
        raise HTTPException(status_code=400, detail="Uyarı mesajı boş olamaz")
    
    async with get_db_connection() as cursor:
        # Get user info
        await cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Create warning notification
        notification_id = str(uuid.uuid4())
        await cursor.execute("""
            INSERT INTO notifications (id, user_id, type, title, message, from_user_id, from_username, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            notification_id,
            user_id,
            "mention",  # Using mention as closest type for admin warning
            "🚨 YÖNETİCİ UYARISI",
            f"🚨 YÖNETİCİ UYARISI: {warning_message}",
            current_user.id,
            current_user.username,
            datetime.now(timezone.utc)
        ))
        
        return {"message": f"{user_info['username']} kullanıcısına uyarı gönderildi"}

@api_router.post("/admin/mute-user/{user_id}")
async def mute_user(
    user_id: str, 
    request: dict,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    mute_hours = request.get('mute_hours', 0)
    if not isinstance(mute_hours, int) or mute_hours < 1:
        raise HTTPException(status_code=400, detail="Geçerli bir saat sayısı girin")
    
    async with get_db_connection() as cursor:
        # Calculate mute until time
        mute_until = datetime.now(timezone.utc) + timedelta(hours=mute_hours)
        
        # Update user
        await cursor.execute("""
            UPDATE users 
            SET is_muted = TRUE, mute_until = %s 
            WHERE id = %s
        """, (mute_until, user_id))
        
        # Get user info
        await cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Create notification
        notification_id = str(uuid.uuid4())
        await cursor.execute("""
            INSERT INTO notifications (id, user_id, type, title, message, from_user_id, from_username, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            notification_id,
            user_id,
            "mention",  # Using mention as closest type
            "🔇 Hesap Susturuldu",
            f"🔇 Hesabınız {mute_hours} saat süreyle sessize alınmıştır. Bu süre içinde soru, cevap veya yanıt gönderemezsiniz. Susturma süresi: {mute_until.strftime('%d.%m.%Y %H:%M')}",
            current_user.id,
            current_user.username,
            datetime.now(timezone.utc)
        ))
        
        return {"message": f"{user_info['username']} kullanıcısı {mute_hours} saat susturuldu"}

@api_router.post("/admin/ban-user/{user_id}")
async def ban_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    
    async with get_db_connection() as cursor:
        # Get user info first
        await cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_info = await cursor.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Delete user completely (CASCADE will handle related data)
        await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        return {"message": f"{user_info['username']} hesabı yasaklandı ve silindi"}

# TEMPORARY: First time admin setup
@api_router.post("/setup-admin")
async def setup_admin():
    """One-time setup to make first admin user"""
    async with get_db_connection() as cursor:
        # Make artez71 admin
        await cursor.execute("""
            UPDATE users SET is_admin = TRUE 
            WHERE username = 'artez71' OR id = '8c7c78da-e6fc-45f1-bf60-ccc6b62107b5'
        """)
        
        # Also make superadmin admin
        await cursor.execute("""
            UPDATE users SET is_admin = TRUE 
            WHERE username = 'superadmin' OR email = 'admin@unisoruyor.com'
        """)
        
# PUBLIC: One-time admin setup (artez71)
# MANUAL: Create admin account endpoint
@api_router.post("/create-admin-account")
async def create_admin_account():
    """Create admin account manually"""
    try:
        async with get_db_connection() as cursor:
            # Check if admin already exists
            await cursor.execute("""
                SELECT id FROM users WHERE email = 'admin@unisoruyor.com'
            """)
            existing = await cursor.fetchone()
            
            if existing:
                return {"success": False, "message": "Admin hesabı zaten mevcut"}
            
            # Create admin
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            admin_id = str(uuid.uuid4())
            hashed_password = pwd_context.hash("Admin123456!")
            
            await cursor.execute("""
                INSERT INTO users (
                    id, email, username, password_hash, university, faculty, department, is_admin, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                admin_id,
                "admin@unisoruyor.com",
                "superadmin", 
                hashed_password,
                "Sistem",
                "Yönetim",
                "Admin",
                True,
                datetime.now(timezone.utc)
            ))
            
            return {
                "success": True,
                "message": "✅ Admin hesabı oluşturuldu!",
                "email": "admin@unisoruyor.com",
                "username": "superadmin",
                "password": "Admin123456!"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def create_default_admin():
    """Create default admin user if not exists"""
    try:
        async with get_db_connection() as cursor:
            # Check if admin user already exists
            await cursor.execute("""
                SELECT id FROM users WHERE email = 'admin@unisoruyor.com' OR username = 'superadmin'
            """)
            admin_exists = await cursor.fetchone()
            
            if not admin_exists:
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                admin_id = str(uuid.uuid4())
                hashed_password = pwd_context.hash("Admin123456!")
                
                await cursor.execute("""
                    INSERT INTO users (
                        id, email, username, password_hash, university, faculty, department, is_admin, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    admin_id,
                    "admin@unisoruyor.com",
                    "superadmin", 
                    hashed_password,
                    "Sistem",
                    "Yönetim",
                    "Admin",
                    True,  # is_admin = True
                    datetime.now(timezone.utc)
                ))
                
                print("✅ Default admin user created!")
                print("📧 Email: admin@unisoruyor.com")
                print("👤 Username: superadmin")
                print("🔑 Password: Admin123456!")
                return True
            else:
                print("ℹ️ Admin user already exists")
                return False
                
    except Exception as e:
        print(f"❌ Error creating default admin: {e}")
        return False

# Startup event to create default admin
@app.on_event("startup")
async def startup_event():
    """Create default admin on startup"""
    await create_default_admin()

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)