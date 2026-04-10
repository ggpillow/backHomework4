import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session as OrmSession

from database import SessionLocal
from models import User, Session as DBSession
from schemas import RegisterRequest, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db: OrmSession = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    db: OrmSession = Depends(get_db),
) -> User:
    if not x_session_id:
        raise HTTPException(status_code=401, detail="Missing X-Session-Id")

    s = db.query(DBSession).filter(DBSession.id == x_session_id).first()
    if not s:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter(User.id == s.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: OrmSession = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=data.username, password_hash=pwd.hash(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: OrmSession = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not pwd.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = str(uuid.uuid4())
    db.add(DBSession(id=session_id, user_id=user.id))
    db.commit()
    return LoginResponse(session_id=session_id)


@router.post("/logout", status_code=204)
def logout(
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    db: OrmSession = Depends(get_db),
):
    if not x_session_id:
        raise HTTPException(status_code=401, detail="Missing X-Session-Id")

    s = db.query(DBSession).filter(DBSession.id == x_session_id).first()
    if not s:
        raise HTTPException(status_code=401, detail="Invalid session")

    db.delete(s)
    db.commit()
    return None