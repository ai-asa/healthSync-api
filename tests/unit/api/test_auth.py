"""
JWT認証機能のユニットテスト
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import pytest
from jose import jwt, JWTError

from src.api.v1.dependencies.auth import (
    create_access_token,
    verify_token,
    get_user_from_token
)
from src.core.security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from src.domain.entities.user import UserInToken


class TestJWTAuthentication:
    """JWT認証のテストクラス"""

    def test_create_access_token_with_user_data(self) -> None:
        """ユーザーデータを含むアクセストークンを生成できる"""
        # Arrange
        user_data = {"sub": "user123", "email": "test@example.com"}
        
        # Act
        token = create_access_token(data=user_data)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # トークンをデコードして内容を確認
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_create_access_token_with_custom_expiry(self) -> None:
        """カスタム有効期限でトークンを生成できる"""
        # Arrange
        user_data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)
        
        # Act
        token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        # Assert
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # 有効期限が約30分後に設定されていることを確認（1分の余裕を持たせる）
        assert timedelta(minutes=29) <= (exp_time - now) <= timedelta(minutes=31)

    def test_verify_token_with_valid_token(self) -> None:
        """有効なトークンを検証できる"""
        # Arrange
        user_data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data=user_data)
        
        # Act
        payload = verify_token(token)
        
        # Assert
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

    def test_verify_token_with_expired_token(self) -> None:
        """期限切れトークンでJWTErrorが発生する"""
        # Arrange
        user_data = {"sub": "user123"}
        # 1秒前に期限切れになるトークンを作成
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        # Act & Assert
        with pytest.raises(JWTError):
            verify_token(token)

    def test_verify_token_with_invalid_token(self) -> None:
        """無効なトークンでJWTErrorが発生する"""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act & Assert
        with pytest.raises(JWTError):
            verify_token(invalid_token)

    def test_verify_token_with_wrong_algorithm(self) -> None:
        """異なるアルゴリズムで署名されたトークンでJWTErrorが発生する"""
        # Arrange
        user_data = {"sub": "user123"}
        # 異なるアルゴリズムでトークンを作成
        token = jwt.encode(user_data, SECRET_KEY, algorithm="HS512")
        
        # Act & Assert
        with pytest.raises(JWTError):
            verify_token(token)

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self) -> None:
        """有効なトークンから現在のユーザーを取得できる"""
        # Arrange
        user_data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data=user_data)
        
        # Act
        user = await get_user_from_token(token)
        
        # Assert
        assert user is not None
        assert isinstance(user, UserInToken)
        assert user.user_id == "user123"
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self) -> None:
        """無効なトークンで認証エラーが発生する"""
        # Arrange
        invalid_token = "invalid.token"
        
        # Act & Assert
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_user_from_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio  
    async def test_get_current_user_with_missing_sub(self) -> None:
        """subフィールドがないトークンで認証エラーが発生する"""
        # Arrange
        # subフィールドなしでトークンを作成
        user_data = {"email": "test@example.com"}  # subなし
        token = create_access_token(data=user_data)
        
        # Act & Assert
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_user_from_token(token)
        
        assert exc_info.value.status_code == 401

    def test_token_expiry_default(self) -> None:
        """デフォルトの有効期限が正しく設定される"""
        # Arrange
        user_data = {"sub": "user123"}
        
        # Act
        token = create_access_token(data=user_data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Assert
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # デフォルトの有効期限が設定されていることを確認（1分の余裕を持たせる）
        actual_delta = exp_time - now
        assert timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES - 1) <= actual_delta <= timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES + 1)