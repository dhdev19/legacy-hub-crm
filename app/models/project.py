from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    nanoid = Column(String(21), nullable=False, unique=True)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    sales_links = relationship("ProjectSales", back_populates="project")
    queries = relationship("Query", back_populates="project")

class ProjectSales(Base):
    __tablename__ = "project_sales"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    project = relationship("Project", back_populates="sales_links")
    user = relationship("User", back_populates="project_links", foreign_keys=[user_id])
