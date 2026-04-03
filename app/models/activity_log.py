from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class ActorRoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    sales = "sales"
    system = "system"

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(100), nullable=True)
    actor_role = Column(Enum(ActorRoleEnum), nullable=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
