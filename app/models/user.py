from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    sales = "sales"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    project_links = relationship("ProjectSales", back_populates="user", foreign_keys="ProjectSales.user_id")
    assigned_queries = relationship("Query", back_populates="assigned_user", foreign_keys="Query.assigned_to")
    followups_created = relationship("FollowUp", back_populates="creator", foreign_keys="FollowUp.created_by")
