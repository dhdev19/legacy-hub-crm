from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectSales
from app.models.query import Query
from app.models.followup import FollowUp
from app.models.source_status import Source, Status
from app.dependencies import require_sales
from app.services.log_service import log_activity
from typing import Optional

router = APIRouter(prefix="/sales")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def sales_dashboard(request: Request, page: int = 1, search: Optional[str] = None,
                    db: Session = Depends(get_db), current_user: User = Depends(require_sales)):
    per_page = 50
    q = db.query(Query).filter(Query.assigned_to == current_user.id, Query.is_deleted == 0).options(
        joinedload(Query.project), joinedload(Query.source),
        joinedload(Query.status), joinedload(Query.followups)
    )
    if search:
        q = q.filter(Query.client_name.ilike(f"%{search}%") | Query.query_name.ilike(f"%{search}%"))
    total = q.count()
    queries = q.order_by(Query.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page
    statuses = db.query(Status).filter(Status.is_deleted == 0).all()
    return templates.TemplateResponse("sales/dashboard.html", {
        "request": request, "user": current_user, "queries": queries,
        "page": page, "total_pages": total_pages, "total": total,
        "statuses": statuses, "search": search or ""
    })

@router.get("/add-query", response_class=HTMLResponse)
def add_query_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_sales)):
    links = db.query(ProjectSales).filter(ProjectSales.user_id == current_user.id).all()
    projects = [l.project for l in links if l.project.is_deleted == 0]
    sources = db.query(Source).filter(Source.is_deleted == 0).all()
    statuses = db.query(Status).filter(Status.is_deleted == 0).all()
    return templates.TemplateResponse("sales/add_query.html", {
        "request": request, "user": current_user,
        "projects": projects, "sources": sources, "statuses": statuses
    })

@router.post("/add-query")
def add_query(query_name: str = Form(...), client_name: str = Form("NA"),
              email: str = Form("NA"), phone: str = Form("NA"),
              project_id: Optional[int] = Form(None), source_id: Optional[int] = Form(None),
              status_id: Optional[int] = Form(None),
              db: Session = Depends(get_db), current_user: User = Depends(require_sales)):
    query = Query(
        query_name=query_name, client_name=client_name or "NA",
        email=email or "NA", phone=phone or "NA",
        project_id=project_id, source_id=source_id,
        status_id=status_id, assigned_to=current_user.id
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    log_activity(db, current_user.id, current_user.name, current_user.role, "created_query", "query", query.id, f"Query: {query_name}")
    return RedirectResponse("/sales/", status_code=302)

@router.post("/query/status/{query_id}")
def update_status(query_id: int, status_id: int = Form(...),
                  db: Session = Depends(get_db), current_user: User = Depends(require_sales)):
    query = db.query(Query).filter(Query.id == query_id, Query.assigned_to == current_user.id, Query.is_deleted == 0).first()
    if not query:
        raise HTTPException(status_code=404)
    query.status_id = status_id
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "updated_query_status", "query", query_id, f"Status -> {status_id}")
    return JSONResponse({"success": True})

@router.post("/followup/add/{query_id}")
def add_followup(query_id: int, remark: str = Form(...), follow_up_dt: str = Form(...),
                 db: Session = Depends(get_db), current_user: User = Depends(require_sales)):
    query = db.query(Query).filter(Query.id == query_id, Query.assigned_to == current_user.id, Query.is_deleted == 0).first()
    if not query:
        raise HTTPException(status_code=404)
    from datetime import datetime
    fu = FollowUp(query_id=query_id, remark=remark,
                  follow_up_dt=datetime.fromisoformat(follow_up_dt),
                  created_by=current_user.id)
    db.add(fu)
    db.commit()
    log_activity(db, current_user.id, current_user.name, current_user.role, "added_followup", "followup", fu.id, f"Followup for query {query_id}")
    return RedirectResponse("/sales/", status_code=302)

@router.get("/projects", response_class=HTMLResponse)
def my_projects(request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_sales)):
    links = db.query(ProjectSales).filter(ProjectSales.user_id == current_user.id).all()
    project_data = []
    for l in links:
        if l.project.is_deleted == 0:
            qcount = db.query(func.count(Query.id)).filter(
                Query.project_id == l.project_id,
                Query.assigned_to == current_user.id,
                Query.is_deleted == 0
            ).scalar()
            project_data.append({"project": l.project, "query_count": qcount})
    return templates.TemplateResponse("sales/projects.html", {
        "request": request, "user": current_user, "project_data": project_data
    })
