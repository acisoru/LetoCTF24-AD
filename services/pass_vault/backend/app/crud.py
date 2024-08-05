from sqlalchemy import text
from sqlalchemy.orm import Session
from . import models, schemas

def get_passwords(db: Session, user_id: int, orderByValue: str):
    return db.query(models.Password).filter(models.Password.user_id == user_id).order_by(text(orderByValue)).all()

def get_password(db: Session, password_id: int):
    return db.query(models.Password).filter(
        models.Password.id == password_id
    ).first()

def create_password(db: Session, password: schemas.PasswordCreate, user_id: int):
    db_password = models.Password(
        website=password.website,
        username=password.username,
        password=password.password,
        user_id=user_id
    )
    db.add(db_password)
    db.commit()
    db.refresh(db_password)
    return db_password

def update_password(db: Session, password_id: int, password: schemas.PasswordBase):
    db_password = get_password(db, password_id)
    if db_password is None:
        return None
    
    for var, value in vars(password).items():
        setattr(db_password, var, value) if value else None
    
    db.add(db_password)
    db.commit()
    db.refresh(db_password)
    return db_password

def delete_password(db: Session, password_id: int):
    db_password = get_password(db, password_id)
    if db_password is None:
        return False
    db.delete(db_password)
    db.commit()
    return True

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str, hashed_password: str) -> models.User:
    db_user = models.User(username=username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
