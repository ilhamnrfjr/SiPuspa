import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "mysql+mysqlconnector://root:@localhost:3306/chatbot_bpk"
)

SECRET_KEY: str = os.getenv("SECRET_KEY", "ganti-dengan-secret-key-aman")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60

CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:5000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5000",
]
