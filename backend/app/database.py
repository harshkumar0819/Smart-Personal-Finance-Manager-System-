
import logging
import time
import uuid

from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    ConfigurationError,
    ServerSelectionTimeoutError,
    PyMongoError
)

from app.config import Config

logger = logging.getLogger(__name__)

_client = None
_db = None


def get_client():
    global _client

    if _client is None:
        uri = Config.MONGODB_URI

        if not uri or not uri.strip():
            raise ConfigurationError(
                "MONGODB_URI is missing. Please check your .env file."
            )

        _client = MongoClient(
            uri.strip(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )

    return _client


def get_db():
    global _db

    if _db is None:
        client = get_client()
        db_name = Config.DB_NAME or "finwise_db"

        if not db_name.strip():
            raise ConfigurationError("Database name is missing.")

        _db = client[db_name.strip()]

    return _db


def check_db_connection():
    if not Config.MONGODB_URI:
        return False, "MongoDB connection is not configured.", {
            "status": "disconnected",
            "read_write": "unavailable"
        }

    start_time = time.time()
    test_id = f"health_{uuid.uuid4().hex}"
    db = None

    try:
        client = get_client()
        client.admin.command("ping")

        db = get_db()
        health_collection = db["_health_checks"]

        health_collection.insert_one({
            "_id": test_id,
            "checked_at": time.time()
        })

        result = health_collection.find_one({"_id": test_id})

        if not result:
            raise PyMongoError("Database read verification failed.")

        latency = round((time.time() - start_time) * 1000, 2)

        return True, "MongoDB connected successfully.", {
            "status": "connected",
            "database": Config.DB_NAME or "finwise_db",
            "read_write": "verified",
            "latency_ms": latency
        }

    except ConfigurationError:
        logger.exception("MongoDB configuration error.")
        return False, "Please check your MongoDB configuration.", {
            "status": "disconnected",
            "read_write": "unavailable"
        }

    except ServerSelectionTimeoutError:
        logger.exception("MongoDB server could not be reached.")
        return False, "MongoDB connection timed out.", {
            "status": "disconnected",
            "read_write": "unavailable"
        }

    except ConnectionFailure:
        logger.exception("MongoDB connection or authentication failed.")
        return False, "Unable to connect or authenticate with MongoDB.", {
            "status": "disconnected",
            "read_write": "unavailable"
        }

    except PyMongoError:
        logger.exception("MongoDB operation failed.")
        return False, "A database operation failed.", {
            "status": "disconnected",
            "read_write": "unavailable"
        }

    except Exception:
        logger.exception("Unexpected database error.")
        return False, "An unexpected error occurred.", {
            "status": "disconnected",
            "read_write": "unavailable"
        }

    finally:
        if db is not None:
            try:
                db["_health_checks"].delete_one({"_id": test_id})
            except PyMongoError:
                logger.warning("Could not remove temporary health-check record.")


def close_db():
    global _client, _db

    if _client is not None:
        _client.close()
        _client = None
        _db = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("SmartFin Manager - Database Connection Test")

    connected, message, details = check_db_connection()

    print(message)
    print(f"Status: {details.get('status')}")

    if connected:
        print(f"Database: {details.get('database')}")
        print(f"Read/Write: {details.get('read_write')}")
        print(f"Latency: {details.get('latency_ms')} ms")

    close_db()
