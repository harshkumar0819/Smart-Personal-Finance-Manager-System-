import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base application configuration loaded from environment variables."""
    _secret_key = os.environ.get('SECRET_KEY')

    # Strictly require SECRET_KEY: must be present, non-None, and non-empty
    if not _secret_key or not _secret_key.strip():
        raise ValueError(
            "Configuration Error: 'SECRET_KEY' environment variable is missing or empty. "
            "Please define a secure, non-empty SECRET_KEY in your .env file."
        )

    SECRET_KEY = _secret_key.strip()
    DEBUG = os.environ.get('FLASK_ENV') == 'development'

    # MongoDB Configuration (Atlas URI from environment, with local fallback for local development)
    _mongo_uri = os.environ.get('MONGODB_URI')
    MONGODB_URI = _mongo_uri.strip() if _mongo_uri and _mongo_uri.strip() else 'mongodb://localhost:27017'
    DB_NAME = os.environ.get('DB_NAME', 'finwise_db')
