from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"


def load_config():
    """Load environment variables from the project .env file."""
    load_dotenv(BASE_DIR / ".env")
    OUTPUT_DIR.mkdir(exist_ok=True)

    return {
        "output_dir": OUTPUT_DIR,
    }
