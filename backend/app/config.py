import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+asyncmy://cloudnotes:cloudnotes123@localhost:3306/cloudnotes"
)
SECRET_KEY = os.getenv("SECRET_KEY", "cloud-notes-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
