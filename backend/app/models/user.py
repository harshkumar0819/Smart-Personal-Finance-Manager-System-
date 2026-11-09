import re
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


def ensure_user_indexes():
    db = get_db()
    db.users.create_index("email", unique=True)


def validate_registration_input(name, email, password, confirm_password):
    if not name or not name.strip():
        return False, "Full Name is required."
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long."
    if len(name.strip()) > 80:
        return False, "Name cannot exceed 80 characters."

    if not email or not email.strip():
        return False, "Email address is required."
    clean_email = email.strip().lower()
    if not EMAIL_REGEX.match(clean_email):
        return False, "Please enter a valid email address (e.g., user@example.com)."

    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."

    if password != confirm_password:
        return False, "Passwords do not match. Please verify your password."

    return True, None


def get_user_by_email(email):
    if not email:
        return None
    db = get_db()
    return db.users.find_one({"email": email.strip().lower()})


def get_user_by_id(user_id):
    if not user_id:
        return None
    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return None

    db = get_db()
    return db.users.find_one({"_id": oid})


def create_user(name, email, password):
    clean_name = name.strip()
    clean_email = email.strip().lower()
    ensure_user_indexes()
    if get_user_by_email(clean_email) is not None:
        return False, "An account with this email address already exists. Please log in.", None
    password_hash = generate_password_hash(password)

    user_doc = {
        "name": clean_name,
        "email": clean_email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc)
    }

    db = get_db()
    try:
        result = db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return True, "User registered successfully.", user_doc
    except DuplicateKeyError:
        return False, "An account with this email address already exists. Please log in.", None
    except Exception as e:
        return False, f"Registration failed due to a database error: {str(e)}", None


def authenticate_user(email, password):
    if not email or not email.strip() or not password:
        return False, "Please provide both email and password.", None

    clean_email = email.strip().lower()
    user = get_user_by_email(clean_email)

    if not user:
        return False, "Invalid email or password.", None

    stored_hash = user.get("password_hash", "")
    if not check_password_hash(stored_hash, password):
        return False, "Invalid email or password.", None

    return True, "Authentication successful.", user
