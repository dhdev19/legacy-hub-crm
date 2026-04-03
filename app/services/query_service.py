from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.query import Query
from app.models.project import ProjectSales

def get_min_query_sales_person(db: Session, project_id: int):
    """Return user_id of sales person on project with fewest active queries."""
    links = db.query(ProjectSales).filter(ProjectSales.project_id == project_id).all()
    if not links:
        return None

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
