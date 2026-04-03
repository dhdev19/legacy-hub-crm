from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    query_name = Column(String(200), nullable=False)
    client_name = Column(String(150), default="NA")
    email = Column(String(150), default="NA")
    phone = Column(String(30), default="NA")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="queries")
    source = relationship("Source")
    status = relationship("Status")
    assigned_user = relationship("User", back_populates="assigned_queries", foreign_keys=[assigned_to])
    followups = relationship("FollowUp", back_populates="query", order_by="FollowUp.follow_up_dt")
