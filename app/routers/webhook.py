from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.query import Query
from app.models.source_status import Source, Status
from app.services.query_service import get_min_query_sales_person
from app.services.log_service import log_activity
from app.services.webhook_service import process_99acres_data, process_magicbricks_data, save_webhook_data
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/webhook")

# API Keys from environment
ACRES_API_KEY = os.getenv("ACRES_API")
MAGIC_API_KEY = os.getenv("MAGIC_API")

@router.post("/99acres")
async def webhook_99acres(request: Request, db: Session = Depends(get_db)):
    """Webhook endpoint for 99acres integration"""
    try:
        # Validate API key
        api_key = request.headers.get("API-Key")
        if api_key != ACRES_API_KEY:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid API key"}
            )
        
        # Get JSON data
        data = await request.json()
        
        # Process the data
        success, message = process_99acres_data(data, db)
        
        # Save webhook data
        save_webhook_data("99acres", data, success, message if not success else None, db)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"success": True, "message": message}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": message}
            )
            
    except Exception as e:
        # Save error data
        try:
            data = await request.json()
            save_webhook_data("99acres", data, False, f"Server error: {str(e)}", db)
        except:
            pass
        
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

@router.post("/magicbricks")
async def webhook_magicbricks(request: Request, db: Session = Depends(get_db)):
    """Webhook endpoint for MagicBricks integration"""
    try:
        # Validate API key
        api_key = request.headers.get("API-Key")
        if api_key != MAGIC_API_KEY:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid API key"}
            )
        
        # Get JSON data
        data = await request.json()
        
        # Process the data
        success, message = process_magicbricks_data(data, db)
        
        # Save webhook data
        save_webhook_data("magicbricks", data, success, message if not success else None, db)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"success": True, "message": message}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": message}
            )
            
    except Exception as e:
        # Save error data
        try:
            data = await request.json()
            save_webhook_data("magicbricks", data, False, f"Server error: {str(e)}", db)
        except:
            pass
        
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

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
