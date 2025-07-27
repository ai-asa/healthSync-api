"""
JWT認証の依存関数
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from src.core.security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from src.domain.entities.user import UserInToken


class HTTPBearer401(HTTPBearer):
    """403の代わりに401を返すカスタムHTTPBearer"""
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """認証ヘッダーがない場合やフォーマットが不正な場合に401を返す"""
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == status.HTTP_403_FORBIDDEN:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise


# Bearer認証スキーム
security = HTTPBearer401()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを生成する
    
    Args:
        data: トークンに含めるデータ
        expires_delta: 有効期限（デフォルトはACCESS_TOKEN_EXPIRE_MINUTES）
        
    Returns:
        エンコードされたJWTトークン
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    JWTトークンを検証する
    
    Args:
        token: 検証するトークン
        
    Returns:
        デコードされたペイロード
        
    Raises:
        JWTError: トークンが無効な場合
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


async def get_user_from_token(token: str) -> UserInToken:
    """
    トークンからユーザー情報を取得する（内部関数）
    
    Args:
        token: JWTトークン
        
    Returns:
        認証済みユーザー情報
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # トークンを検証
        payload = verify_token(token)
        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        # UserInTokenオブジェクトを作成
        user = UserInToken(
            user_id=user_id,
            email=payload.get("email")
        )
        
        return user
        
    except JWTError:
        raise credentials_exception


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInToken:
    """
    現在の認証済みユーザーを取得する（FastAPIエンドポイント用）
    
    Args:
        credentials: HTTPAuthorizationCredentials（Bearerトークン）
        
    Returns:
        認証済みユーザー情報
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    return await get_user_from_token(credentials.credentials)