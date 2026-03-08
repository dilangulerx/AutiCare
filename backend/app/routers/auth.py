from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token, UserUpdate
from app.services.auth import register_user, authenticate_user, create_access_token, decode_token, get_user_by_id

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    return user

@router.post("/register", response_model=UserResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(db, data.email, data.name, data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı")
    return user

@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name: current_user.name = data.name
    if data.email: current_user.email = data.email
    if data.phone: current_user.phone = data.phone
    if data.password:
        from app.services.auth import hash_password
        current_user.hashed_password = hash_password(data.password)
    db.commit()
    db.refresh(current_user)
    return current_user