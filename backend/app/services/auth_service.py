from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import bcrypt
import json
from pathlib import Path
from app.core.config import settings

# Путь к файлу пользователей
USERS_FILE = Path(__file__).parent.parent.parent / "users.json"


class AuthService:
    """Сервис для авторизации и работы с JWT токенами"""

    def __init__(self):
        self.users = self._load_users()

    def _load_users(self) -> Dict:
        """Загрузить пользователей из JSON файла"""
        try:
            if USERS_FILE.exists():
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {user['username']: user for user in data.get('users', [])}
            else:
                print(f"[Warning] Users file not found: {USERS_FILE}")
                return {}
        except Exception as e:
            print(f"[Error] Failed to load users: {e}")
            return {}

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """Получить хеш пароля"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Аутентифицировать пользователя

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Данные пользователя или None
        """
        user = self.users.get(username)
        if not user:
            return None

        if not self.verify_password(password, user['password_hash']):
            return None

        return user

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

    def decode_token(self, token: str) -> Optional[Dict]:
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

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Получить пользователя по username"""
        return self.users.get(username)


# Singleton instance
auth_service = AuthService()
