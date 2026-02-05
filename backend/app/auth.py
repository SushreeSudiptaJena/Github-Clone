import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from .db import get_session
from .crud import get_user_by_username
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class TokenData(BaseModel):
    username: Optional[str] = None


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_password_reset_token(username: str, expires_minutes: int = 15) -> str:
    to_encode = {"sub": username}
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "reset": True})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> str:
    credentials_exception = HTTPException(
        status_code=400,
        detail="Invalid or expired reset token",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        is_reset = payload.get("reset", False)
        if not username or not is_reset:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(lambda: None), db: AsyncSession = Depends(get_session)) -> User:
    """This dependency is used in routes; for standard requests the token will be provided via header handling in the endpoint.
    For simplicity we expect the route to pass the Authorization header value via FastAPI's dependency injection.
    """
    # This function is intended to be used with a wrapper that extracts Authorization header.
    raise HTTPException(status_code=500, detail="get_current_user should be used with a dependency wrapper")


async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user_by_username(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Helper for FastAPI header-based dependency
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Security, Request
from fastapi.security.utils import get_authorization_scheme_param

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

async def get_current_user_header(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> User:
    return await get_user_from_token(token, db)
