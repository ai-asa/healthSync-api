"""
ユーザーエンティティ定義
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserInToken(BaseModel):
    """JWTトークンに含まれるユーザー情報"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    user_id: str = Field(..., description="ユーザーID")
    email: Optional[EmailStr] = Field(None, description="メールアドレス")
    
    
class User(BaseModel):
    """ユーザーエンティティ（将来の拡張用）"""
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    id: str = Field(..., description="ユーザーID")
    email: EmailStr = Field(..., description="メールアドレス")
    is_active: bool = Field(True, description="アクティブフラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")