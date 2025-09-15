from .auth import auth_bp
from .user import user_bp
from .admin import admin_bp

# export all blueprints so app.py can import them easily
__all__ = ["auth_bp", "user_bp", "admin_bp"]
