
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from ..config.config import SECRET_KEY
from enum import Enum


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class AllowedScope(str, ExtendedEnum):
    SEND_LOGS = "SEND_LOGS"
    READ_LOGS = "READ_LOGS"
    USER_ADMIN = "USER_ADMIN"


allowedScopesDescription = {
    AllowedScope.SEND_LOGS.value: "Allow to send logs",
    AllowedScope.READ_LOGS.value: "Allow to read logs",
    AllowedScope.USER_ADMIN.value: "Allows to add and update users"
}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", scopes=allowedScopesDescription)

def verify_password(plain_password, hashed_password):
    print(plain_password, hashed_password, get_password_hash(plain_password))
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        return False


def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

