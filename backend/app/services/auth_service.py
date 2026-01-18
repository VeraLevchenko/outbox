from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings
from app.models.database import SessionLocal
from app.models.user import User


class AuthService:
    """Сервис для авторизации и работы с JWT токенами"""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Получить хеш пароля"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Аутентифицировать пользователя

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Данные пользователя или None
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None

            if not self.verify_password(password, user.hashed_password):
                return None

            return {
                "username": user.username,
                "role": user.role,
                "id": user.id
            }
        finally:
            db.close()

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Создать JWT токен

        Args:
            data: Данные для токена
            expires_delta: Время жизни токена

        Returns:
            JWT токен
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        return encoded_jwt

    def decode_token(self, token: str) -> Optional[dict]:
        """
        Декодировать JWT токен

        Args:
            token: JWT токен

        Returns:
            Данные из токена или None
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Получить пользователя по username"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None

            return {
                "username": user.username,
                "role": user.role,
                "id": user.id
            }
        finally:
            db.close()


# Singleton instance
auth_service = AuthService()
