from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
import json

def log_activity(db: Session, actor_id, actor_name, actor_role, action, entity=None, entity_id=None, detail=None):
    if isinstance(detail, dict):
        detail = json.dumps(detail)
    log = ActivityLog(
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail
    )
    db.add(log)
    db.commit()
