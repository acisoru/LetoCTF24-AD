from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class PasswordBase(BaseModel):
    website: str
    username: str
    password: str

class PasswordRead(BaseModel):
    id: int
    website: str
    username: str
    password: str
    
class PasswordCreate(PasswordBase):
    pass

class Password(PasswordBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
