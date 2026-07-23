from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminUser
from app.schemas import UserCreate, UserUpdate
from app.auth import hash_password
from app.routers.deps import get_current_user, require_role

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/")
def list_users(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    rows = db.query(AdminUser).order_by(AdminUser.id).all()
    return {
        "users": [
            {
                "id": r.id,
                "username": r.username,
                "full_name": r.full_name,
                "role": r.role,
                "is_active": r.is_active,
                "created_at": str(r.created_at) if r.created_at else None,
                "last_login": str(r.last_login) if r.last_login else None,
            }
            for r in rows
        ]
    }


@router.post("/")
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("superadmin")),
):
    existing = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
    new_user = AdminUser(
        username=req.username,
        password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
        is_active=1,
    )
    db.add(new_user)
    db.commit()
    return {"success": True, "message": "User ditambahkan", "id": new_user.id}


@router.put("/{user_id}")
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("superadmin")),
):
    u = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    u.full_name = req.full_name
    u.role = req.role
    db.commit()
    return {"success": True, "message": "User diupdate"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("superadmin")),
):
    u = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if u.id == user["id"]:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus akun sendiri")
    db.delete(u)
    db.commit()
    return {"success": True, "message": "User dihapus"}


@router.post("/{user_id}/toggle-active")
def toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("superadmin")),
):
    u = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    u.is_active = 0 if u.is_active else 1
    db.commit()
    return {"success": True, "is_active": u.is_active}
