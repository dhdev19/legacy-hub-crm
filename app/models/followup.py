from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    remark = Column(Text, nullable=False)
    follow_up_dt = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    query = relationship("Query", back_populates="followups")
    creator = relationship("User", back_populates="followups_created", foreign_keys=[created_by])
