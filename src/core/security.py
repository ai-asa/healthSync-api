"""
セキュリティ関連の設定
"""
import os
from typing import Optional
from passlib.context import CryptContext


# JWT設定
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# パスワードハッシュ設定（将来の拡張用）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証する"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化する"""
    return pwd_context.hash(password)