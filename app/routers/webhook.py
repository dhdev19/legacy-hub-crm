from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.query import Query
from app.models.source_status import Source, Status
from app.services.query_service import get_min_query_sales_person
from app.services.log_service import log_activity

router = APIRouter(prefix="/webhook")

@router.post("/{project_nanoid}/query")
async def webhook_query(project_nanoid: str, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.nanoid == project_nanoid, Project.is_deleted == 0).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        data = await request.json()
    except Exception:
        data = {}

    query_name = data.get("query_name") or data.get("name") or f"Webhook-{project_nanoid}"
    client_name = data.get("client_name") or data.get("name") or "NA"
    email = data.get("email") or "NA"
    phone = data.get("phone") or data.get("mobile") or "NA"
    source_name = data.get("source") or "Webhook"

    source = db.query(Source).filter(Source.name == source_name, Source.is_deleted == 0).first()
    if not source:
        source = Source(name=source_name)
        db.add(source)
        db.commit()
        db.refresh(source)

    assigned_to = get_min_query_sales_person(db, project.id)

    query = Query(
        query_name=query_name, client_name=client_name,
        email=email, phone=phone,
        project_id=project.id, source_id=source.id,
        assigned_to=assigned_to
    )
    db.add(query)
    db.commit()
    db.refresh(query)

    log_activity(db, None, "system", "system", "webhook_query_created", "query", query.id,
                 f"Webhook query for project {project.name}, assigned_to={assigned_to}")

    return JSONResponse({"success": True, "query_id": query.id, "assigned_to": assigned_to})
