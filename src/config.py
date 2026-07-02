from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"


def load_config():
    """Load environment variables from the project .env file."""
    load_dotenv(BASE_DIR / ".env")
    OUTPUT_DIR.mkdir(exist_ok=True)

    return {
        "output_dir": OUTPUT_DIR,
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-5.5"),
        "openai_api_base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    }
