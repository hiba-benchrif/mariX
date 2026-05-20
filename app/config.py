import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # Configuration BDD : on gère la spécificité Railway postgres:// -> postgresql://
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///marix.db')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Sécurité et limites
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit for uploads
    PERMANENT_SESSION_LIFETIME = 1800  # 30 min
    SESSION_COOKIE_SECURE = True  # True en production (HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True
