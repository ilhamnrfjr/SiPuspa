from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoginRequest, ChangePasswordRequest
from app.auth import login_user, verify_token, logout_user, change_password
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    result = login_user(db, req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Username atau password salah")
    return result


@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return {"valid": True, "user": user}


@router.post("/logout")
def logout(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
        logout_user(db, token)
    return {"success": True, "message": "Logout berhasil"}


@router.post("/change-password")
def change_pw(
    req: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = change_password(db, user["id"], req.old_password, req.new_password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
