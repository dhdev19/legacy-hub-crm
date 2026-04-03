from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.models.user import User
from app.services.auth_service import decode_token

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=302, headers={"Location": "/login"})
        user = db.query(User).filter(User.id == int(user_id), User.is_deleted == 0).first()
        if not user:
            raise HTTPException(status_code=302, headers={"Location": "/login"})
        return user
    except JWTError:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

def require_superadmin(current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_sales(current_user: User = Depends(get_current_user)):
    if current_user.role != "sales":
        raise HTTPException(status_code=403, detail="Sales access required")
    return current_user
