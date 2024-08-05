from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from .auth import login, register, logout, get_current_user
from .schemas import *
from . import crud
from .database import get_db

router = APIRouter()

@router.post("/api/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return register(db, user)

@router.post("/api/login")
def login_user(response: Response, user: UserCreate, db: Session = Depends(get_db)):
    return login(response, db, user)

@router.get("/api/logout")
def logout_user(response: Response):
    return logout(response)

@router.get("/api/passwords", response_model=List[PasswordRead])
def read_passwords(current_user: UserBase = Depends(get_current_user), orderByValue: Optional[str] = "id", db: Session = Depends(get_db)):
    return crud.get_passwords(db, current_user.id, orderByValue=orderByValue)

@router.post("/api/passwords", response_model=PasswordRead)
def create_password(password: PasswordCreate, current_user: UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_password(db, password, current_user.id)

@router.get("/api/passwords/{password_id}", response_model=PasswordRead)
def read_password(password_id: int, current_user: UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    password = crud.get_password(db, password_id)
    if password is None:
        raise HTTPException(status_code=404, detail="Password not found")
    return password
    
@router.put("/api/passwords/{password_id}", response_model=PasswordBase)
def update_password(password_id: int, password: PasswordBase, current_user: UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    updated_password = crud.update_password(db, password_id, password)
    if updated_password is None:
        raise HTTPException(status_code=404, detail="Password not found")
    return updated_password

@router.delete("/api/passwords/{password_id}")
def delete_password(password_id: int, current_user: UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    if not crud.delete_password(db, password_id):
        raise HTTPException(status_code=404, detail="Password not found")
    return {"message": "Password deleted successfully"}
