from typing import List
from fastapi import APIRouter, Security
from pydantic import ValidationError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from jose import JWTError, jwt
from datetime import timedelta

from ..database.userprovider import User, UserProvider
from ..authutils.authutils import verify_password, oauth2_scheme, SECRET_KEY, ALGORITHM, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, AllowedScope
from ..serviceprovider import getServiceProvider
from .models.authmodel import Token, TokenData

router = APIRouter()

async def getUserProvider():
    return getServiceProvider().userProvider

async def authenticate_user(userProvider: UserProvider, username: str, password: str):
    user = userProvider.getUser(username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


async def user_has_privileges(user: User, form_data_scopes: List[str]):

    for scope in form_data_scopes:
        if(scope not in AllowedScope.list() or scope not in user.privileges):
            return False
    return True

async def get_current_user(security_scopes: SecurityScopes, userProvider: UserProvider = Depends(getUserProvider), token: str = Depends(oauth2_scheme)):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    user = userProvider.getUser(token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


@router.post("/token", response_model=Token, summary="Generate access token")
async def login_for_access_token(userProvider = Depends(getUserProvider), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(userProvider, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    shouldProvideAccess = await user_has_privileges(user, form_data.scopes)

    if(not shouldProvideAccess):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )


    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
