from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    """Запрос на вход в систему"""
    username: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "levchenko",
                "password": "логин123"
            }
        }


class TokenResponse(BaseModel):
    """Ответ с токеном доступа"""
    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class UserData(BaseModel):
    """Данные пользователя"""
    id: int
    username: str
    full_name: str
    role: str


class TokenWithUserResponse(BaseModel):
    """Ответ с токеном и данными пользователя"""
    access_token: str
    token_type: str = "bearer"
    user: UserData

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "director",
                    "full_name": "director",
                    "role": "director"
                }
            }
        }


class UserResponse(BaseModel):
    """Информация о пользователе"""
    username: str
    full_name: str
    role: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "levchenko",
                "full_name": "Левченко В.С.",
                "role": "director"
            }
        }
