"""
Database models using SQLAlchemy
"""

from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml

Base = declarative_base()


class Dataset(Base):
    """Dataset metadata"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    format = Column(String(50), nullable=False)
    total_records = Column(Integer, default=0)
    valid_records = Column(Integer, default=0)
    industry_tags = Column(JSON, default=list)
    copy_types = Column(JSON, default=list)
    status = Column(String(50), default="uploaded")  # uploaded, cleaned, split
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Training split info
    train_path = Column(String(512), nullable=True)
    val_path = Column(String(512), nullable=True)
    split_ratio = Column(Float, default=0.8)


class LoRAModel(Base):
    """Fine-tuned LoRA model metadata"""
    __tablename__ = "lora_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    base_model = Column(String(255), nullable=False)
    lora_path = Column(String(512), nullable=False)
    merged_path = Column(String(512), nullable=True)
    industry_tag = Column(String(100), nullable=True)
    dataset_id = Column(Integer, nullable=True)
    status = Column(String(50), default="training")  # training, completed, error
    lora_r = Column(Integer, default=8)
    lora_alpha = Column(Integer, default=16)
    train_samples = Column(Integer, default=0)
    eval_samples = Column(Integer, default=0)
    train_loss = Column(Float, nullable=True)
    training_time = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationRecord(Base):
    """Generation history"""
    __tablename__ = "generation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, nullable=True)
    source_content = Column(Text, nullable=False)
    generated_content = Column(Text, nullable=False)
    industry_tag = Column(String(100), nullable=True)
    copy_type = Column(String(50), nullable=True)
    is_edited = Column(Boolean, default=False)
    edited_content = Column(Text, nullable=True)
    bleu_score = Column(Float, nullable=True)
    rouge_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OperationLog(Base):
    """Operation logs"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String(100), nullable=False)  # dataset_upload, train, generate, etc.
    operation_details = Column(Text, nullable=True)
    status = Column(String(50), default="success")  # success, failed
    error_message = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """User (single-user mode)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db(db_path: str = "./data/ad_helper.db"):
    """Initialize database"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_default_db_path() -> str:
    """Get default database path from config"""
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            return config.get("system", {}).get("db_path", "./data/ad_helper.db")
    except:
        return "./data/ad_helper.db"
