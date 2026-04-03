from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, RoleEnum
from app.models.activity_log import ActivityLog
from app.dependencies import require_superadmin
from app.services.auth_service import hash_password
from app.services.log_service import log_activity

router = APIRouter(prefix="/superadmin")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def superadmin_dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_superadmin)):
    admins = db.query(User).filter(User.role == "admin", User.is_deleted == 0).all()
    return templates.TemplateResponse("superadmin/dashboard.html", {"request": request, "user": current_user, "admins": admins})

@router.post("/admin/add")
def add_admin(request: Request, name: str = Form(...), username: str = Form(...), password: str = Form(...),
              db: Session = Depends(get_db), current_user: User = Depends(require_superadmin)):
    existing = db.query(User).filter(User.username == username, User.is_deleted == 0).first()
    if existing:
        admins = db.query(User).filter(User.role == "admin", User.is_deleted == 0).all()
        return templates.TemplateResponse("superadmin/dashboard.html", {"request": request, "user": current_user, "admins": admins, "error": "Username already exists"})
    new_admin = User(name=name, role=RoleEnum.admin, username=username, password_hash=hash_password(password))
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    log_activity(db, current_user.id, current_user.name, current_user.role, "created_admin", "user", new_admin.id, f"Created admin: {name} ({username})")
    return RedirectResponse("/superadmin/", status_code=302)

@router.post("/admin/edit/{admin_id}")
def edit_admin(admin_id: int, name: str = Form(...), password: str = Form(None),
               db: Session = Depends(get_db), current_user: User = Depends(require_superadmin)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin", User.is_deleted == 0).first()
    if not admin:
        raise HTTPException(status_code=404)
    admin.name = name
    if password and password.strip():
        admin.password_hash = hash_password(password)
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "edited_admin", "user", admin_id, f"Edited admin: {name}")
    return RedirectResponse("/superadmin/", status_code=302)

@router.post("/admin/delete/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_superadmin)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin", User.is_deleted == 0).first()
    if not admin:
        raise HTTPException(status_code=404)
    admin.is_deleted = 1
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "deleted_admin", "user", admin_id, f"Deleted admin: {admin.name}")
    return RedirectResponse("/superadmin/", status_code=302)

@router.get("/logs", response_class=HTMLResponse)
def activity_logs(request: Request, page: int = 1, db: Session = Depends(get_db), current_user: User = Depends(require_superadmin)):
    per_page = 50
    total = db.query(ActivityLog).count()
    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    return templates.TemplateResponse("superadmin/activity_logs.html", {
        "request": request, "user": current_user, "logs": logs,
        "page": page, "total_pages": total_pages, "total": total
    })
