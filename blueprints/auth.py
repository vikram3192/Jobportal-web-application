from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import db_cursor
import re

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

# -------------------- HELPERS --------------------
def api_response(success, message, **kwargs):
    """Standard JSON response"""
    data = {"success": success, "message": message}
    if kwargs:
        data.update(kwargs)
    return jsonify(data)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_mobile(mobile):
    return mobile.isdigit() and len(mobile) == 10


def validate_password(password):
    # Password policy: min 8 chars, 1 uppercase, 1 lowercase, 1 digit
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
    )

# =========================================================
# -------------------- USER REGISTER ----------------------
# =========================================================
@auth_bp.route("/register", methods=["POST"])
def api_register():
    if not request.is_json:
        return api_response(False, "Request must be JSON"), 400

    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    mobile = data.get("mobile")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not all([name, email, mobile, password, confirm_password]):
        return api_response(False, "Missing required fields"), 400
    if password != confirm_password:
        return api_response(False, "Passwords do not match"), 400
    if not validate_email(email):
        return api_response(False, "Invalid email format"), 400
    if not validate_mobile(mobile):
        return api_response(False, "Invalid mobile number"), 400
    if not validate_password(password):
        return api_response(
            False,
            "Password must be at least 8 characters long, "
            "with 1 uppercase, 1 lowercase, and 1 digit"
        ), 400

    hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE email=%s OR mobile=%s LIMIT 1",
                (email, mobile),
            )
            if cursor.fetchone():
                return api_response(False, "Email or Mobile already registered"), 400

        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "INSERT INTO users (name, email, mobile, password) VALUES (%s, %s, %s, %s)",
                (name, email, mobile, hashed_pw),
            )
    except Exception as e:
        return api_response(False, f"Database error: {str(e)}"), 500

    return api_response(True, "User registration successful")

# =========================================================
# -------------------- EMPLOYER REGISTER ------------------
# =========================================================
@auth_bp.route("/employer/register", methods=["POST"])
def api_employer_register():
    if not request.is_json:
        return api_response(False, "Request must be JSON"), 400

    data = request.get_json()
    employer_name = data.get("employer_name")
    organization_name = data.get("organization_name")
    organization_email = data.get("organization_email")
    mobile = data.get("mobile")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not all([employer_name, organization_name, organization_email, password, confirm_password]):
        return api_response(False, "Missing required fields"), 400
    if password != confirm_password:
        return api_response(False, "Passwords do not match"), 400
    if not validate_email(organization_email):
        return api_response(False, "Invalid organization email"), 400
    if mobile and not validate_mobile(mobile):
        return api_response(False, "Invalid mobile number"), 400
    if not validate_password(password):
        return api_response(False, "Weak password"), 400

    hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")

    try:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM employers WHERE organization_email=%s OR mobile=%s LIMIT 1",
                (organization_email, mobile),
            )
            if cursor.fetchone():
                return api_response(False, "Email or Mobile already registered"), 400

        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """INSERT INTO employers (employer_name, organization_name, organization_email, mobile, password)
                   VALUES (%s, %s, %s, %s, %s)""",
                (employer_name, organization_name, organization_email, mobile, hashed_pw),
            )
    except Exception as e:
        return api_response(False, f"Database error: {str(e)}"), 500

    return api_response(True, "Employer registration successful")

# =========================================================
# -------------------- USER LOGIN -------------------------
# =========================================================
@auth_bp.route("/login", methods=["POST"])
def api_login():
    if not request.is_json:
        return api_response(False, "Request must be JSON"), 400

    data = request.get_json()
    identifier = data.get("identifier")  # email or mobile
    password = data.get("password")

    if not identifier or not password:
        return api_response(False, "Missing identifier or password"), 400

    try:
        with db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE (email=%s OR mobile=%s)",
                (identifier, identifier),
            )
            user = cursor.fetchone()
    except Exception:
        return api_response(False, "Database error"), 500

    if user and check_password_hash(user["password"], password):
        session["user"] = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "mobile": user["mobile"],
            "role": "User"
        }
        return api_response(True, "Login successful", user=session["user"])
    else:
        return api_response(False, "Invalid credentials"), 401

# =========================================================
# -------------------- EMPLOYER LOGIN ---------------------
# =========================================================
@auth_bp.route("/employer/login", methods=["POST"])
def api_employer_login():
    if not request.is_json:
        return api_response(False, "Request must be JSON"), 400

    data = request.get_json()
    identifier = data.get("identifier")  # org email or mobile
    password = data.get("password")

    if not identifier or not password:
        return api_response(False, "Missing identifier or password"), 400

    try:
        with db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM employers WHERE (organization_email=%s OR mobile=%s)",
                (identifier, identifier),
            )
            employer = cursor.fetchone()
    except Exception:
        return api_response(False, "Database error"), 500

    if employer and check_password_hash(employer["password"], password):
        session["user"] = {
            "id": employer["id"],
            "employer_name": employer["employer_name"],
            "organization_name": employer["organization_name"],
            "organization_email": employer["organization_email"],
            "mobile": employer["mobile"],
            "role": "Employer",  
            "logo_filename": employer.get("logo_filename"), 
        }
        return api_response(True, "Login successful", user=session["user"])  
    else:
        return api_response(False, "Invalid credentials"), 401

# =========================================================
# -------------------- LOGOUT -----------------------------
# =========================================================
@auth_bp.route("/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)  
    return api_response(True, "Logged out")

# -------------------- SESSION ----------------------------
@auth_bp.route("/session", methods=["GET"])
def api_session():
    if "user" in session:
        return api_response(True, "Session active", user=session["user"])
    return api_response(False, "No active session"), 401
