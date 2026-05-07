import os
from pathlib import Path

from dotenv import load_dotenv


# The project root is one level above the src directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
VECTOR_STORE_NAME = os.getenv(
    "VECTOR_STORE_NAME",
    "league-of-legends-knowledge-base",
)

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VECTOR_STORE_ID_FILE = PROJECT_ROOT / "vector_store_id.txt"


def ensure_directories() -> None:
    """Create the folders used by the scripts if they do not exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def require_openai_api_key() -> str:
    """Return the OpenAI API key or raise a clear setup error."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Create a .env file from .env.example first."
        )
    return OPENAI_API_KEY


def require_youtube_api_key() -> str:
    """Return the YouTube Data API key or raise a clear setup error."""
    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "Missing YOUTUBE_API_KEY. Create a YouTube Data API key and add it to .env."
        )
    return YOUTUBE_API_KEY


ensure_directories()
