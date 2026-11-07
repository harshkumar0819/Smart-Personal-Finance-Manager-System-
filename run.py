
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        debug=app.config.get("DEBUG", False),
        port=5000
    )
