import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from dotenv import load_dotenv
import os

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- SECRET KEY ----------------
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev_secret")

# ---------------- DATABASE CONFIG ----------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "jobportal"),
    "pool_name": "mypool",
    "pool_size": 5,
    "pool_reset_session": True
  }

# Optional: Connection pool (better for production)
try:
    connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
except Exception:
    connection_pool = None  # fallback to direct connect

def get_db():
    """Return a new database connection (use pool if available)."""
    if connection_pool:
        return connection_pool.get_connection()
    return mysql.connector.connect(**DB_CONFIG)

@contextmanager
def db_cursor(dictionary=False, commit=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

# ---------------- FILE UPLOAD CONFIG ----------------
BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

PROFILE_PIC_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "profile_pics")
RESUME_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "resumes")
LOGO_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "logos")

# Ensure folders exist
os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)

# Allowed extensions
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_FILE_SIZE=2*1024*1024

def allowed_file(filename, allowed_extensions):
    """Generic file extension check"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions

# Convenience wrappers
def allowed_image_file(filename):
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)

def allowed_resume_file(filename):
    return allowed_file(filename, ALLOWED_RESUME_EXTENSIONS)
