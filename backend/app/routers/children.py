from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.child import Child
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/children", tags=["Children"])

def get_child_or_404(child_id: int, db: Session, current_user):
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Çocuk bulunamadı")
    return child

@router.post("", response_model=ChildResponse)
def create_child(data: ChildCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    child = Child(parent_id=current_user.id, **data.model_dump())
    db.add(child)
    db.commit()
    db.refresh(child)
    return child

@router.get("", response_model=List[ChildResponse])
def get_children(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Child).filter(Child.parent_id == current_user.id).all()

@router.get("/{child_id}", response_model=ChildResponse)
def get_child(child_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return get_child_or_404(child_id, db, current_user)

@router.put("/{child_id}", response_model=ChildResponse)
def update_child(child_id: int, data: ChildUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    child = get_child_or_404(child_id, db, current_user)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(child, key, value)
    db.commit()
    db.refresh(child)
    return child

@router.delete("/{child_id}")
def delete_child(child_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    child = get_child_or_404(child_id, db, current_user)
    db.delete(child)
    db.commit()
    return {"message": "Çocuk silindi"}