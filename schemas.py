from pydantic import BaseModel
from typing import Optional


class StudentCreate(BaseModel):
    last_name: str
    first_name: str
    faculty: str
    course: str
    grade: int


class StudentUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[str] = None
    grade: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    last_name: str
    first_name: str
    faculty: str
    course: str
    grade: int

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    session_id: str