from datetime import datetime, timedelta
from secrets import token_urlsafe

import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import AdminUser, AdminSession


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_default_superadmin(db: Session):
    existing = db.query(AdminUser).first()
    if existing:
        return
    user = AdminUser(
        username="superadmin",
        password=hash_password("Admin@BPK2025"),
        full_name="Super Administrator",
        role="superadmin",
        is_active=1,
    )
    db.add(user)

    user2 = AdminUser(
        username="admin_puspa",
        password=hash_password("Puspa@2025"),
        full_name="Admin PUSPA",
        role="admin",
        is_active=1,
    )
    db.add(user2)
    db.commit()


def login_user(db: Session, username: str, password: str):
    user = db.query(AdminUser).filter(
        AdminUser.username == username,
        AdminUser.is_active == 1
    ).first()
    if not user or not verify_password(password, user.password):
        return None

    token = token_urlsafe(32)
    expires_at = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    session = AdminSession(user_id=user.id, token=token, expires_at=expires_at)
    db.add(session)
    user.last_login = datetime.now()
    db.commit()

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
        },
    }


def verify_token(db: Session, token: str):
    if not token:
        return None
    session = db.query(AdminSession).filter(
        AdminSession.token == token,
        AdminSession.expires_at > datetime.now()
    ).first()
    if not session:
        return None
    user = db.query(AdminUser).filter(AdminUser.id == session.user_id).first()
    if not user or not user.is_active:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }


def logout_user(db: Session, token: str):
    db.query(AdminSession).filter(AdminSession.token == token).delete()
    db.commit()


def change_password(db: Session, user_id: int, old_password: str, new_password: str):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user or not verify_password(old_password, user.password):
        return {"success": False, "message": "Password lama salah"}
    user.password = hash_password(new_password)
    db.commit()
    return {"success": True, "message": "Password berhasil diubah"}
