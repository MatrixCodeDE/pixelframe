import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
secret_key = secrets.token_hex(32)
algorithm = "HS256"
token_expire_minutes = 10
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(user: str):
    """
    Erstellt nach erfolgreichem Anmelden einen JWT
    Args:
        user: Modell Login (siehe models/loginmodels)

    Returns:
        den JWT für den Nutzer
    """
    encoded = {"sub": user}
    if token_expire_minutes:
        expire = datetime.utcnow() + timedelta(minutes=token_expire_minutes)
    else:
        expire = datetime.utcnow() + timedelta(minutes=10)
    encoded.update({"exp": expire})
    encoded_jwt = jwt.encode(encoded, secret_key, algorithm=algorithm)
    return encoded_jwt


def get_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Get the user from a given token
    Args:
        token: JWT

    Returns:
        user

    Raises:
        HTTPException
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user = payload.get("sub")
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user


def get_admin(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Returns True if the user is an admin (currently always true since admin is only registered user)

    Returns:
        True

    Raises:
        HTTPException
    """
    get_user(token)
    return True
