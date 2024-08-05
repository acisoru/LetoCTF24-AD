from fastapi import Depends, HTTPException, status, Cookie, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import get_db
from .schemas import UserCreate, User
import hashlib, random, datetime, string
import jwt

security = HTTPBearer(auto_error=False)

random.seed(521337)
SECRET_KEY = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32))
ALGORITHM = "HS256"


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user or user.password != hashlib.sha256(password.encode()).hexdigest():
        return None
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def register(db: Session, user: UserCreate) -> User:
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    db_user = crud.create_user(db, user.username, hashed_password)
    return User(id=db_user.id, username=db_user.username)

def login(response: Response, db: Session, user: schemas.UserBase):
    db_user = authenticate_user(db, user.username, user.password)
    
    if db_user is None:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token_data = {
        "sub": db_user.username,
        "id": db_user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }

    token = create_access_token(token_data)

    response.set_cookie(key="access_token", value=f"{token}", httponly=False)
    
    return {"message": "Login Successful"}

def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logout Successful"}

def get_current_user(
    authorization: HTTPAuthorizationCredentials = Depends(security),
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    if not authorization and not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = authorization.credentials if authorization else access_token
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
