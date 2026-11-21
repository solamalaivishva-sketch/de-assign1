#Reading settings from project .env file

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

RAW_DIR = PROJECT_ROOT / "data" / "raw" # Bronze
SILVER_DIR = PROJECT_ROOT / "data" / "silver" # Silver   
LOG_DIR = PROJECT_ROOT / "logs"

PG_DSN =(
    f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
    f"port={os.getenv('POSTGRES_PORT', '5432')} "
    f"dbname={os.getenv('POSTGRES_DB', 'taxi_dw')} "
    f"user={os.getenv('POSTGRES_USER', 'taxi')} "
    f"password={os.getenv('POSTGRES_PASSWORD', 'taxi_pass')}"


)
