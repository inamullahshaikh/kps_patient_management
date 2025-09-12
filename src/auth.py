import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .schema import Person
from .database import collections
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
print(SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 360

# Use bcrypt (ensure passlib[bcrypt] is installed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# auto_error=False allows unauthenticated requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate_user(username: str, password: str) -> Optional[Person]:
    """
    Returns a Person if username/password match, else None.
    """
    user_doc = await collections["persons"].find_one({"username": username})
    if not user_doc:
        return None
    user = Person(**user_doc)
    if not verify_password(password, user.password):
        return None
    return user


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Person]:
    """
    Returns Person from token WITHOUT verifying signature.
    Only for testing / local development.
    """
    if not token:
        return None  # allow unauthenticated access

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        print("Token received:", token)
        # Decode WITHOUT verifying signature
        payload = jwt.decode(token, key=None, algorithms=None, options={"verify_signature": False})
        print("JWT payload:", payload)
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_doc = await collections["persons"].find_one({"username": username})
    if user_doc is None:
        raise credentials_exception
    if "DOB" in user_doc and isinstance(user_doc["DOB"], datetime):
        user_doc["DOB"] = user_doc["DOB"].isoformat()
    print("DONE")
    print(user_doc)
    person = Person(**user_doc)
    return person



async def get_current_active_user(current_user: Person = Depends(get_current_user)) -> Person:
    """
    Ensures user is authenticated.
    """
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user
