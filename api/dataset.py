"""
FastAPI routes for Dataset operations
"""

import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel

from dataset.process import DatasetProcessor, DatasetStats
from api.database import Dataset, OperationLog, init_db, get_default_db_path

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

# Global DB session
_engine, _Session = None, None


def get_session():
    global _engine, _Session
    if _Session is None:
        db_path = get_default_db_path()
        _engine, _Session = init_db(db_path)
    return _Session()


# Request/Response models
class DatasetResponse(BaseModel):
    id: int
    name: str
    file_path: str
    format: str
    total_records: int
    valid_records: int
    status: str
    created_at: str


class CleanRequest(BaseModel):
    dataset_id: int


class SplitRequest(BaseModel):
    dataset_id: int
    split_ratio: float = 0.8


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...)
):
    """Upload a dataset file (JSON or JSONL)"""
    session = get_session()

    # Validate file format
    allowed_formats = [".json", ".jsonl"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_formats:
        raise HTTPException(400, f"Unsupported format: {file_ext}")

    # Save file
    upload_dir = Path("./data/datasets")
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_name = f"{timestamp}_{file.filename}"
    file_path = upload_dir / saved_name

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Process and validate
    processor = DatasetProcessor()
    try:
        records = processor.load_dataset(str(file_path))
    except Exception as e:
        raise HTTPException(400, f"Failed to load dataset: {str(e)}")

    # Clean and get stats
    cleaned = processor.clean_dataset(records)
    stats = DatasetStats.get_stats(cleaned["records"])

    # Save to database
    dataset = Dataset(
        name=name,
        file_path=str(file_path),
        format=file_ext.replace(".", ""),
        total_records=stats["total"],
        valid_records=cleaned["stats"]["valid"],
        industry_tags=list(stats["by_industry"].keys()),
        copy_types=list(stats["by_copy_type"].keys()),
        status="uploaded"
    )
    session.add(dataset)
    session.commit()

    # Log operation
    log = OperationLog(
        operation_type="dataset_upload",
        operation_details=f"Uploaded dataset '{name}' with {stats['total']} records",
        status="success"
    )
    session.add(log)
    session.commit()

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        file_path=dataset.file_path,
        format=dataset.format,
        total_records=dataset.total_records,
        valid_records=dataset.valid_records,
        status=dataset.status,
        created_at=dataset.created_at.isoformat()
    )


@router.get("/list")
async def list_datasets():
    """List all datasets"""
    session = get_session()
    datasets = session.query(Dataset).order_by(Dataset.created_at.desc()).all()

    return [
        {
            "id": d.id,
            "name": d.name,
            "format": d.format,
            "total_records": d.total_records,
            "valid_records": d.valid_records,
            "status": d.status,
            "industry_tags": d.industry_tags,
            "created_at": d.created_at.isoformat()
        }
        for d in datasets
    ]


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int):
    """Get dataset details"""
    session = get_session()
    dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    return {
        "id": dataset.id,
        "name": dataset.name,
        "file_path": dataset.file_path,
        "format": dataset.format,
        "total_records": dataset.total_records,
        "valid_records": dataset.valid_records,
        "industry_tags": dataset.industry_tags,
        "copy_types": dataset.copy_types,
        "status": dataset.status,
        "train_path": dataset.train_path,
        "val_path": dataset.val_path,
        "split_ratio": dataset.split_ratio,
        "created_at": dataset.created_at.isoformat()
    }


@router.post("/clean")
async def clean_dataset(request: CleanRequest):
    """Clean a dataset (remove duplicates, violations)"""
    session = get_session()
    dataset = session.query(Dataset).filter(Dataset.id == request.dataset_id).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    processor = DatasetProcessor()
    records = processor.load_dataset(dataset.file_path)
    result = processor.clean_dataset(records)

    # Update dataset status
    dataset.status = "cleaned"
    dataset.valid_records = result["stats"]["valid"]
    session.commit()

    return {
        "dataset_id": dataset.id,
        "stats": result["stats"],
        "status": "cleaned"
    }


@router.post("/split")
async def split_dataset(request: SplitRequest):
    """Split dataset into train and validation sets"""
    session = get_session()
    dataset = session.query(Dataset).filter(Dataset.id == request.dataset_id).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    if dataset.status != "cleaned":
        raise HTTPException(400, "Dataset must be cleaned before splitting")

    processor = DatasetProcessor()
    records = processor.load_dataset(dataset.file_path)
    cleaned = processor.clean_dataset(records)

    train_records, val_records = processor.split_dataset(
        cleaned["records"],
        split_ratio=request.split_ratio
    )

    # Save split files
    split_dir = Path(f"./data/splits/{dataset.id}")
    split_dir.mkdir(parents=True, exist_ok=True)

    train_path = split_dir / "train.jsonl"
    val_path = split_dir / "val.jsonl"

    processor.save_dataset(train_records, str(train_path), "jsonl")
    processor.save_dataset(val_records, str(val_path), "jsonl")

    # Update dataset
    dataset.train_path = str(train_path)
    dataset.val_path = str(val_path)
    dataset.split_ratio = request.split_ratio
    dataset.status = "split"
    session.commit()

    return {
        "dataset_id": dataset.id,
        "train_path": str(train_path),
        "val_path": str(val_path),
        "train_count": len(train_records),
        "val_count": len(val_records),
        "status": "split"
    }


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int):
    """Delete a dataset"""
    session = get_session()
    dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Delete files
    if Path(dataset.file_path).exists():
        Path(dataset.file_path).unlink()
    if dataset.train_path and Path(dataset.train_path).exists():
        Path(dataset.train_path).unlink()
    if dataset.val_path and Path(dataset.val_path).exists():
        Path(dataset.val_path).unlink()

    session.delete(dataset)
    session.commit()

    return {"message": "Dataset deleted", "id": dataset_id}
