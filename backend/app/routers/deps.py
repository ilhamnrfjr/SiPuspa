from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import verify_token


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split("Bearer ")[1]
    user = verify_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Token invalid atau expired")
    return user


def require_role(role: str):
    async def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return role_checker
