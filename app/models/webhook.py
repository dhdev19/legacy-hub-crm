from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class WebhookData(Base):
    __tablename__ = "webhook_data"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # '99acres' or 'magicbricks'
    is_processed = Column(Boolean, default=False)  # True if data was added to queries, False if error
    raw_data = Column(Text, nullable=False)  # Full JSON data received
    error_message = Column(Text, nullable=True)  # Error details if processing failed
    created_at = Column(DateTime, server_default=func.now())
