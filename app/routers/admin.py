from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query as QueryParam
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.database import get_db
from app.models.user import User, RoleEnum
from app.models.project import Project, ProjectSales
from app.models.query import Query
from app.models.followup import FollowUp
from app.models.source_status import Source, Status
from app.dependencies import require_admin
from app.services.auth_service import hash_password
from app.services.log_service import log_activity
from app.services.project_service import generate_project_nanoid
from app.services.query_service import get_min_query_sales_person
from typing import Optional
import json

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

# ── Dashboard / Queries ────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request, page: int = 1, project_id: Optional[int] = None,
                    search: Optional[str] = None, db: Session = Depends(get_db),
                    current_user: User = Depends(require_admin)):
    per_page = 50
    q = db.query(Query).filter(Query.is_deleted == 0).options(
        joinedload(Query.project), joinedload(Query.source),
        joinedload(Query.status), joinedload(Query.assigned_user),
        joinedload(Query.followups)
    )
    if project_id:
        q = q.filter(Query.project_id == project_id)
    if search:
        q = q.filter(Query.client_name.ilike(f"%{search}%") | Query.query_name.ilike(f"%{search}%"))
    total = q.count()
    queries = q.order_by(Query.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    projects = db.query(Project).filter(Project.is_deleted == 0).all()
    statuses = db.query(Status).filter(Status.is_deleted == 0).all()
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "user": current_user, "queries": queries,
        "page": page, "total_pages": total_pages, "total": total,
        "projects": projects, "statuses": statuses,
        "selected_project": project_id, "search": search or ""
    })

# ── Sales Persons ──────────────────────────────────────────────────────────────

@router.get("/sales", response_class=HTMLResponse)
def view_sales(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    sales = db.query(User).filter(User.role == "sales", User.is_deleted == 0).all()
    sales_data = []
    for s in sales:
        proj_count = db.query(func.count(ProjectSales.id)).filter(ProjectSales.user_id == s.id).scalar()
        query_count = db.query(func.count(Query.id)).filter(Query.assigned_to == s.id, Query.is_deleted == 0).scalar()
        sales_data.append({"user": s, "project_count": proj_count, "query_count": query_count})
    return templates.TemplateResponse("admin/sales_persons.html", {"request": request, "user": current_user, "sales_data": sales_data})

@router.post("/sales/add")
def add_sales(name: str = Form(...), username: str = Form(...), password: str = Form(...),
              db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    existing = db.query(User).filter(User.username == username, User.is_deleted == 0).first()
    if existing:
        return RedirectResponse("/admin/sales?error=Username+already+exists", status_code=302)
    sp = User(name=name, role=RoleEnum.sales, username=username, password_hash=hash_password(password))
    db.add(sp)
    db.commit()
    db.refresh(sp)
    log_activity(db, current_user.id, current_user.name, current_user.role, "created_sales", "user", sp.id, f"Created sales: {name}")
    return RedirectResponse("/admin/sales", status_code=302)

@router.post("/sales/edit/{user_id}")
def edit_sales(user_id: int, name: str = Form(...), password: str = Form(None),
               db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    sp = db.query(User).filter(User.id == user_id, User.role == "sales", User.is_deleted == 0).first()
    if not sp:
        raise HTTPException(status_code=404)
    sp.name = name
    if password and password.strip():
        sp.password_hash = hash_password(password)
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "edited_sales", "user", user_id, f"Edited sales: {name}")
    return RedirectResponse("/admin/sales", status_code=302)

@router.get("/sales/delete-info/{user_id}")
def sales_delete_info(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    sp = db.query(User).filter(User.id == user_id, User.role == "sales", User.is_deleted == 0).first()
    if not sp:
        raise HTTPException(status_code=404)
    count = db.query(func.count(Query.id)).filter(Query.assigned_to == user_id, Query.is_deleted == 0).scalar()
    return JSONResponse({"name": sp.name, "query_count": count})

@router.post("/sales/delete/{user_id}")
def delete_sales(user_id: int, action: str = Form(...),
                 db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    sp = db.query(User).filter(User.id == user_id, User.role == "sales", User.is_deleted == 0).first()
    if not sp:
        raise HTTPException(status_code=404)
    queries = db.query(Query).filter(Query.assigned_to == user_id, Query.is_deleted == 0).all()
    if action == "transfer":
        for q in queries:
            q.assigned_to = None
            q.project_id = None
    else:
        for q in queries:
            db.query(FollowUp).filter(FollowUp.query_id == q.id).update({"is_deleted": 1})
            q.is_deleted = 1
    db.query(ProjectSales).filter(ProjectSales.user_id == user_id).delete()
    sp.is_deleted = 1
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "deleted_sales", "user", user_id, f"Deleted sales: {sp.name}, action={action}")
    return RedirectResponse("/admin/sales", status_code=302)

# ── Projects ───────────────────────────────────────────────────────────────────

@router.get("/projects", response_class=HTMLResponse)
def view_projects(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    projects = db.query(Project).filter(Project.is_deleted == 0).options(joinedload(Project.sales_links)).all()
    all_sales = db.query(User).filter(User.role == "sales", User.is_deleted == 0).all()
    project_data = []
    for p in projects:
        sales_on_project = [link.user for link in p.sales_links]
        query_count = db.query(func.count(Query.id)).filter(Query.project_id == p.id, Query.is_deleted == 0).scalar()
        project_data.append({"project": p, "sales": sales_on_project, "query_count": query_count})
    return templates.TemplateResponse("admin/projects.html", {
        "request": request, "user": current_user,
        "project_data": project_data, "all_sales": all_sales
    })

@router.post("/projects/add")
def add_project(name: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    nanoid = generate_project_nanoid()
    project = Project(name=name, nanoid=nanoid)
    db.add(project)
    db.commit()
    db.refresh(project)
    log_activity(db, current_user.id, current_user.name, current_user.role, "created_project", "project", project.id, f"Created project: {name}")
    return RedirectResponse("/admin/projects", status_code=302)

@router.post("/projects/edit/{project_id}")
def edit_project(project_id: int, name: str = Form(...),
                 db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == 0).first()
    if not project:
        raise HTTPException(status_code=404)
    project.name = name
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "edited_project", "project", project_id, f"Renamed project to: {name}")
    return RedirectResponse("/admin/projects", status_code=302)

@router.post("/projects/{project_id}/add-sales")
def add_sales_to_project(project_id: int, user_id: int = Form(...),
                          db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    existing = db.query(ProjectSales).filter(ProjectSales.project_id == project_id, ProjectSales.user_id == user_id).first()
    if not existing:
        link = ProjectSales(project_id=project_id, user_id=user_id)
        db.add(link)
        db.commit()
        log_activity(db, current_user.id, current_user.name, current_user.role, "added_sales_to_project", "project", project_id, f"Added user_id={user_id}")
    return RedirectResponse("/admin/projects", status_code=302)

@router.post("/projects/{project_id}/remove-sales/{user_id}")
def remove_sales_from_project(project_id: int, user_id: int,
                               db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db.query(ProjectSales).filter(ProjectSales.project_id == project_id, ProjectSales.user_id == user_id).delete()
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "removed_sales_from_project", "project", project_id, f"Removed user_id={user_id}")
    return RedirectResponse("/admin/projects", status_code=302)

@router.post("/projects/delete/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == 0).first()
    if not project:
        raise HTTPException(status_code=404)
    db.query(Query).filter(Query.project_id == project_id, Query.is_deleted == 0).update({"project_id": None, "assigned_to": None})
    db.query(ProjectSales).filter(ProjectSales.project_id == project_id).delete()
    project.is_deleted = 1
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "deleted_project", "project", project_id, f"Deleted project: {project.name}")
    return RedirectResponse("/admin/projects", status_code=302)

# ── Queries ────────────────────────────────────────────────────────────────────

@router.get("/query/add", response_class=HTMLResponse)
def add_query_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    projects = db.query(Project).filter(Project.is_deleted == 0).all()
    sources = db.query(Source).filter(Source.is_deleted == 0).all()
    statuses = db.query(Status).filter(Status.is_deleted == 0).all()
    sales = db.query(User).filter(User.role == "sales", User.is_deleted == 0).all()
    return templates.TemplateResponse("admin/add_query.html", {
        "request": request, "user": current_user,
        "projects": projects, "sources": sources, "statuses": statuses, "sales": sales
    })

@router.get("/query/sales-for-project/{project_id}")
def sales_for_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    links = db.query(ProjectSales).filter(ProjectSales.project_id == project_id).all()
    result = [{"id": l.user.id, "name": l.user.name} for l in links if l.user.is_deleted == 0]
    return JSONResponse(result)

@router.post("/query/add")
def add_query(query_name: str = Form(...), client_name: str = Form("NA"),
              email: str = Form("NA"), phone: str = Form("NA"),
              project_id: Optional[int] = Form(None), source_id: Optional[int] = Form(None),
              status_id: Optional[int] = Form(None), assigned_to: Optional[int] = Form(None),
              db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    query = Query(
        query_name=query_name, client_name=client_name or "NA",
        email=email or "NA", phone=phone or "NA",
        project_id=project_id, source_id=source_id,
        status_id=status_id, assigned_to=assigned_to
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    log_activity(db, current_user.id, current_user.name, current_user.role, "created_query", "query", query.id, f"Query: {query_name}")
    return RedirectResponse("/admin/", status_code=302)

@router.get("/query/edit/{query_id}", response_class=HTMLResponse)
def edit_query_page(query_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    query = db.query(Query).filter(Query.id == query_id, Query.is_deleted == 0).first()
    if not query:
        raise HTTPException(status_code=404)
    projects = db.query(Project).filter(Project.is_deleted == 0).all()
    sources = db.query(Source).filter(Source.is_deleted == 0).all()
    statuses = db.query(Status).filter(Status.is_deleted == 0).all()
    all_sales = db.query(User).filter(User.role == "sales", User.is_deleted == 0).all()
    return templates.TemplateResponse("admin/edit_query.html", {
        "request": request, "user": current_user, "query": query,
        "projects": projects, "sources": sources, "statuses": statuses, "all_sales": all_sales
    })

@router.post("/query/edit/{query_id}")
def edit_query(query_id: int, query_name: str = Form(...), client_name: str = Form("NA"),
               email: str = Form("NA"), phone: str = Form("NA"),
               project_id: Optional[int] = Form(None), source_id: Optional[int] = Form(None),
               status_id: Optional[int] = Form(None), assigned_to: Optional[int] = Form(None),
               db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    query = db.query(Query).filter(Query.id == query_id, Query.is_deleted == 0).first()
    if not query:
        raise HTTPException(status_code=404)
    query.query_name = query_name
    query.client_name = client_name or "NA"
    query.email = email or "NA"
    query.phone = phone or "NA"
    query.project_id = project_id
    query.source_id = source_id
    query.status_id = status_id
    query.assigned_to = assigned_to
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "edited_query", "query", query_id, f"Edited query: {query_name}")
    return RedirectResponse("/admin/", status_code=302)

@router.post("/query/delete/{query_id}")
def delete_query(query_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    query = db.query(Query).filter(Query.id == query_id, Query.is_deleted == 0).first()
    if not query:
        raise HTTPException(status_code=404)
    db.query(FollowUp).filter(FollowUp.query_id == query_id).update({"is_deleted": 1})
    query.is_deleted = 1
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "deleted_query", "query", query_id, f"Deleted query: {query.query_name}")
    return RedirectResponse("/admin/", status_code=302)

@router.post("/query/status/{query_id}")
def update_query_status(query_id: int, status_id: int = Form(...),
                        db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    query = db.query(Query).filter(Query.id == query_id, Query.is_deleted == 0).first()
    if not query:
        raise HTTPException(status_code=404)
    query.status_id = status_id
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "updated_query_status", "query", query_id, f"Status changed to {status_id}")
    return JSONResponse({"success": True})

# ── Follow-ups ─────────────────────────────────────────────────────────────────

@router.post("/followup/add/{query_id}")
def add_followup(query_id: int, remark: str = Form(...), follow_up_dt: str = Form(...),
                 db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    from datetime import datetime
    fu = FollowUp(query_id=query_id, remark=remark,
                  follow_up_dt=datetime.fromisoformat(follow_up_dt),
                  created_by=current_user.id)
    db.add(fu)
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "added_followup", "followup", fu.id, f"Followup for query {query_id}")
    return RedirectResponse(f"/admin/?page=1", status_code=302)

# ── Sources & Statuses ─────────────────────────────────────────────────────────

@router.get("/sources", response_class=HTMLResponse)
def manage_sources(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    sources = db.query(Source).filter(Source.is_deleted == 0).all()
    return templates.TemplateResponse("admin/sources.html", {"request": request, "user": current_user, "sources": sources})

@router.post("/sources/add")
def add_source(name: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    s = Source(name=name)
    db.add(s)
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "added_source", "source", s.id, f"Source: {name}")
    return RedirectResponse("/admin/sources", status_code=302)

@router.post("/sources/delete/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    s = db.query(Source).filter(Source.id == source_id).first()
    if s:
        s.is_deleted = 1
        db.commit()
    return RedirectResponse("/admin/sources", status_code=302)

@router.get("/statuses", response_class=HTMLResponse)
def manage_statuses(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    statuses = db.query(Status).filter(Status.is_deleted == 0).all()
    return templates.TemplateResponse("admin/statuses.html", {"request": request, "user": current_user, "statuses": statuses})

@router.post("/statuses/add")
def add_status(name: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    s = Status(name=name)
    db.add(s)
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "added_status", "status", s.id, f"Status: {name}")
    return RedirectResponse("/admin/statuses", status_code=302)

@router.post("/statuses/delete/{status_id}")
def delete_status(status_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    s = db.query(Status).filter(Status.id == status_id).first()
    if s:
        s.is_deleted = 1
        db.commit()
    return RedirectResponse("/admin/statuses", status_code=302)
