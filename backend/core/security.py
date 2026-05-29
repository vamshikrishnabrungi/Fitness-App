"""Auth helpers: JWT, password hashing, current-user dependency."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import ACCESS_TOKEN_EXPIRE_DAYS, JWT_ALGORITHM, JWT_SECRET
from backend.core.db import db

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = dict(data)
    to_encode['exp'] = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = await db.users.find_one({'id': user_id})
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return user


def user_response(user: dict) -> dict:
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'mode': user.get('mode', 'user'),
        'profile': user.get('profile', {}),
        'created_at': user.get('created_at'),
    }


def user_mode(user: dict) -> str:
    return str(user.get('mode') or 'user').strip().lower()


def require_coach_user(current_user: dict) -> None:
    if user_mode(current_user) != 'coach':
        raise HTTPException(status_code=403, detail='Coach access required')


def require_client_user(current_user: dict) -> None:
    if user_mode(current_user) == 'coach':
        raise HTTPException(status_code=403, detail='Client access required')


def deep_clean(value: Any) -> Any:
    """Recursively strip _id keys from nested mongo documents."""
    if isinstance(value, list):
        return [deep_clean(item) for item in value]
    if isinstance(value, dict):
        return {k: deep_clean(v) for k, v in value.items() if k != '_id'}
    return value
