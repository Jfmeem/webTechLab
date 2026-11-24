import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User


router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="login")
db_dependency = Annotated[Session, Depends(get_db)]
ALGORITHM = "HS256"

secret_key = os.environ["JWT_SECRET_KEY"]


def authenticate_user(username, password, db):
    user = db.query(User).filter(User.username == username).first()
    if user is not None and bcrypt_context.verify(password, user.hash_password):
        return user
    return None


def create_access_token(username, user_id, role, expires_in):
    payload = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_in,
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    user_id = payload.get("id")
    role = payload.get("role")
    if username is None or user_id is None or role is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"username": username, "user_id": user_id, "role": role}


@router.post("/login")
def login_user(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}
