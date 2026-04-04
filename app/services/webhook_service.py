from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.query import Query
from app.models.source_status import Source
from app.models.webhook import WebhookData
from app.models.project import Project
from app.models.project import ProjectSales
from app.models.user import User
import json
from datetime import datetime
import re
from difflib import SequenceMatcher

def find_best_project_match(project_name: str, db: Session) -> int:
    """Find the best matching project by name using fuzzy string matching"""
    if not project_name:
        return None
    
    # Get all active projects
    projects = db.query(Project).filter(Project.is_deleted == 0).all()
    
    if not projects:
        return None
    
    best_match = None
    best_ratio = 0.0
    
    # Clean the input project name
    clean_input = re.sub(r'[^\w\s]', '', project_name.lower().strip())
    
    for project in projects:
        # Clean the database project name
        clean_db_name = re.sub(r'[^\w\s]', '', project.name.lower().strip())
        
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, clean_input, clean_db_name).ratio()
        
        # Also check if input is contained in db name or vice versa
        if clean_input in clean_db_name or clean_db_name in clean_input:
            ratio = max(ratio, 0.8)  # Boost score for containment
        
        if ratio > best_ratio and ratio > 0.6:  # Minimum 60% match
            best_ratio = ratio
            best_match = project.id
    
    return best_match

def get_min_query_sales_person_general(db: Session) -> int:
    """Return user_id of sales person with fewest active queries across all projects"""
    # Get all sales users
    sales_users = db.query(User).filter(User.role == "sales", User.is_deleted == 0).all()
    
    if not sales_users:
        return None
    
    min_count = None
    min_user_id = None
    
    for user in sales_users:
        count = db.query(func.count(Query.id)).filter(
            Query.assigned_to == user.id,
            Query.is_deleted == 0
        ).scalar()
        
        if min_count is None or count < min_count:
            min_count = count
            min_user_id = user.id
    
    return min_user_id

def get_min_query_sales_person_for_project(db: Session, project_id: int) -> int:
    """Return user_id of sales person on specific project with fewest active queries"""
    links = db.query(ProjectSales).filter(ProjectSales.project_id == project_id).all()
    if not links:
        # If no specific assignment for this project, return general sales person
        return get_min_query_sales_person_general(db)

    min_count = None
    min_user_id = None

    for link in links:
        count = db.query(func.count(Query.id)).filter(
            Query.assigned_to == link.user_id,
            Query.is_deleted == 0
        ).scalar()
        if min_count is None or count < min_count:
            min_count = count
            min_user_id = link.user_id

    return min_user_id

def process_99acres_data(data: dict, db: Session) -> tuple[bool, str]:
    """Process 99acres webhook data and create query if valid"""
    try:
        # Validate required fields
        required_fields = ['name', 'mobile']
        for field in required_fields:
            if not data.get(field):
                return False, f"Missing required field: {field}"
        
        # Get or create 99acres source
        source = db.query(Source).filter(Source.name == "99acres").first()
        if not source:
            source = Source(name="99acres")
            db.add(source)
            db.commit()
            db.refresh(source)
        
        # Find best matching project
        project_id = find_best_project_match(data.get('project', ''), db)
        
        # Get the sales person with minimum queries
        if project_id:
            assigned_to = get_min_query_sales_person_for_project(db, project_id)
        else:
            assigned_to = get_min_query_sales_person_general(db)
        
        # Create query
        query = Query(
            query_name=f"99acres - {data.get('project', 'N/A')}",
            client_name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('countryCode', '') + data.get('mobile', ''),
            project_id=project_id,
            source_id=source.id,
            status_id=None,  # Will use default status
            assigned_to=assigned_to
        )
        
        db.add(query)
        db.commit()
        db.refresh(query)
        
        return True, f"Query created successfully with ID: {query.id}"
        
    except Exception as e:
        db.rollback()
        return False, f"Error processing data: {str(e)}"

def process_magicbricks_data(data: dict, db: Session) -> tuple[bool, str]:
    """Process MagicBricks webhook data and create query if valid"""
    try:
        # Validate required fields
        required_fields = ['name', 'mobile']
        for field in required_fields:
            if not data.get(field):
                return False, f"Missing required field: {field}"
        
        # Get or create MagicBricks source
        source = db.query(Source).filter(Source.name == "MagicBricks").first()
        if not source:
            source = Source(name="MagicBricks")
            db.add(source)
            db.commit()
            db.refresh(source)
        
        # Find best matching project
        project_id = find_best_project_match(data.get('project', ''), db)
        
        # Get the sales person with minimum queries
        if project_id:
            assigned_to = get_min_query_sales_person_for_project(db, project_id)
        else:
            assigned_to = get_min_query_sales_person_general(db)
        
        # Create query
        query = Query(
            query_name=f"MagicBricks - {data.get('project', 'N/A')}",
            client_name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('countryCode', '') + data.get('mobile', ''),
            project_id=project_id,
            source_id=source.id,
            status_id=None,  # Will use default status
            assigned_to=assigned_to
        )
        
        db.add(query)
        db.commit()
        db.refresh(query)
        
        return True, f"Query created successfully with ID: {query.id}"
        
    except Exception as e:
        db.rollback()
        return False, f"Error processing data: {str(e)}"

def save_webhook_data(source: str, data: dict, is_processed: bool, error_message: str = None, db: Session = None):
    """Save webhook data to database"""
    webhook_entry = WebhookData(
        source=source,
        is_processed=is_processed,
        raw_data=json.dumps(data),
        error_message=error_message
    )
    db.add(webhook_entry)
    db.commit()
