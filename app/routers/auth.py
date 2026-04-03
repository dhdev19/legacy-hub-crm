from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth_service import verify_password, create_access_token
from app.services.log_service import log_activity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.is_deleted == 0).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

    token = create_access_token({"sub": str(user.id), "role": user.role})
    log_activity(db, user.id, user.name, user.role, "login", "user", user.id, f"{user.name} logged in")

    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=86400*7)
    return response

@router.get("/dashboard")
def dashboard_redirect(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login", status_code=302)
    try:
        from app.services.auth_service import decode_token
        payload = decode_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"]), User.is_deleted == 0).first()
        if not user:
            return RedirectResponse("/login", status_code=302)
        if user.role == "superadmin":
            return RedirectResponse("/superadmin/", status_code=302)
        elif user.role == "admin":
            return RedirectResponse("/admin/", status_code=302)
        else:
            return RedirectResponse("/sales/", status_code=302)
    except Exception:
        return RedirectResponse("/login", status_code=302)

@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        try:
            from app.services.auth_service import decode_token
            payload = decode_token(token)
            user = db.query(User).filter(User.id == int(payload["sub"])).first()
            if user:
                log_activity(db, user.id, user.name, user.role, "logout", "user", user.id, f"{user.name} logged out")
        except Exception:
            pass
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response
