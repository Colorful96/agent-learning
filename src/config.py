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
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "deepseek_api_base": os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
    }
