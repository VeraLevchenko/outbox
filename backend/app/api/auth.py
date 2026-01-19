from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from app.services.auth_service import auth_service
from app.schemas.auth_schemas import LoginRequest, TokenResponse, UserResponse, TokenWithUserResponse, UserData
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency для получения текущего пользователя из JWT токена

    Raises:
        HTTPException: Если токен невалидный
    """
    token = credentials.credentials
    payload = auth_service.decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/login", response_model=TokenWithUserResponse)
async def login(login_data: LoginRequest):
    """
    Вход в систему

    Args:
        login_data: Логин и пароль

    Returns:
        JWT токен доступа и данные пользователя

    Raises:
        HTTPException: Если логин или пароль неверны
    """
    user = auth_service.authenticate_user(login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user['username'], "role": user['role']},
        expires_delta=access_token_expires
    )

    return TokenWithUserResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserData(
            id=user['id'],
            username=user['username'],
            full_name=user['full_name'],
            role=user['role']
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Получить информацию о текущем авторизованном пользователе

    Args:
        current_user: Текущий пользователь (из токена)

    Returns:
        Информация о пользователе
    """
    return UserResponse(
        username=current_user['username'],
        full_name=current_user['full_name'],
        role=current_user['role']
    )
