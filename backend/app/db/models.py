from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class ROIHistory(Base):
    __tablename__ = "roi_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    x_min = Column(Float)
    y_min = Column(Float)
    x_max = Column(Float)
    y_max = Column(Float)
    timestamp = Column(DateTime, default=func.now(), index=True)
