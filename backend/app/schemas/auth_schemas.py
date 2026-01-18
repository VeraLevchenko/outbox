from pydantic import BaseModel


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


class UserResponse(BaseModel):
    """Информация о пользователе"""
    username: str
    full_name: str | None = None
    role: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "levchenko",
                "full_name": "Левченко В.С.",
                "role": "director"
            }
        }


class TokenResponse(BaseModel):
    """Ответ с токеном доступа"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "username": "levchenko",
                    "full_name": "Левченко Вера",
                    "role": "director"
                }
            }
        }

