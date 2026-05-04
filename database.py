from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./agency_os.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# The ROI Generator Table
class AutomationLog(Base):
    __tablename__ = "automation_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, index=True)
    time_saved_minutes = Column(Float)
    revenue_generated_euro = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# NEW: The AI Memory Vault
class ClientContext(Base):
    __tablename__ = "client_context"
    id = Column(Integer, primary_key=True, index=True)
    brand_voice = Column(String, default="Professional, helpful, and concise.")
    negative_rules = Column(String, default="Do not make promises about delivery dates. Never offer discounts without approval.")

Base.metadata.create_all(bind=engine)