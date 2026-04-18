"""
FastAPI routes for LoRA training operations
"""

import threading
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from lora.trainer import LoRATrainer, TrainingProgressCallback
from dataset.process import DatasetProcessor
from api.database import LoRAModel, OperationLog, init_db, get_default_db_path
from utils.hardware_detect import detect_hardware, get_gpu_info

router = APIRouter(prefix="/api/lora", tags=["lora"])

_engine, _Session = None, None

# Global trainer instance
_trainer_instance = None
_training_callback = None


def get_session():
    global _engine, _Session
    if _Session is None:
        db_path = get_default_db_path()
        _engine, _Session = init_db(db_path)
    return _Session()


class TrainRequest(BaseModel):
    dataset_id: int
    name: str
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    num_train_epochs: int = 3
    per_device_batch_size: int = 2
    learning_rate: float = 2e-4
    industry_tag: Optional[str] = None


class TrainStatusResponse(BaseModel):
    status: str
    progress: float
    current_step: int
    total_steps: int
    train_loss: Optional[float]
    eval_loss: Optional[float]
    elapsed_time: float
    eta: Optional[float]


# Training state
_training_state = {
    "is_running": False,
    "progress": 0.0,
    "current_step": 0,
    "total_steps": 0,
    "train_loss": None,
    "eval_loss": None,
    "start_time": None,
    "error": None
}


def run_training(dataset_id: int, model_id: int, config: dict):
    """Run training in background thread"""
    global _training_state, _training_callback

    session = get_session()
    dataset = session.query(LoRAModel.__bases__[0]).filter_by(id=dataset_id).first()

    try:
        _training_state["is_running"] = True
        _training_state["start_time"] = time.time()
        _training_state["error"] = None

        # Load dataset
        processor = DatasetProcessor()
        from api.dataset import Dataset
        dataset_obj = session.query(Dataset).filter(Dataset.id == dataset_id).first()
        train_records = processor.load_dataset(dataset_obj.train_path)
        val_records = processor.load_dataset(dataset_obj.val_path)

        # Initialize trainer
        hardware_mode = detect_hardware()
        trainer = LoRATrainer(config_path="config.yaml")

        # Apply config overrides
        trainer.lora_config.r = config["lora_r"]
        trainer.lora_config.lora_alpha = config["lora_alpha"]
        trainer.lora_config.lora_dropout = config["lora_dropout"]
        trainer.training_config.num_train_epochs = config["num_train_epochs"]
        trainer.training_config.per_device_train_batch_size = config["per_device_batch_size"]
        trainer.training_config.learning_rate = config["learning_rate"]

        quantize = hardware_mode in ["QLoRA", "CPU"]
        trainer.load_model(quantize=quantize)
        trainer.setup_lora()

        # Setup callback
        _training_callback = TrainingProgressCallback()

        # Calculate total steps
        _training_state["total_steps"] = len(train_records) // config["per_device_batch_size"] * config["num_train_epochs"]

        # Train
        result = trainer.train(
            train_records=train_records,
            val_records=val_records,
            output_dir=f"./output/lora/{model_id}",
            callbacks=[_training_callback]
        )

        # Update model record
        model = session.query(LoRAModel).filter(LoRAModel.id == model_id).first()
        model.status = "completed"
        model.train_loss = result["train_loss"]
        model.train_samples = len(train_records)
        model.eval_samples = len(val_records)
        model.training_time = time.time() - _training_state["start_time"]
        session.commit()

        _training_state["progress"] = 100.0
        _training_state["is_running"] = False

    except Exception as e:
        _training_state["error"] = str(e)
        _training_state["is_running"] = False

        model = session.query(LoRAModel).filter(LoRAModel.id == model_id).first()
        model.status = "error"
        session.commit()


@router.post("/train")
async def start_training(request: TrainRequest, background_tasks: BackgroundTasks):
    """Start LoRA training"""
    global _training_state

    if _training_state["is_running"]:
        raise HTTPException(400, "Training already in progress")

    session = get_session()

    # Validate dataset
    from api.dataset import Dataset
    dataset = session.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset or dataset.status != "split":
        raise HTTPException(400, "Dataset not ready (must be cleaned and split)")

    # Create model record
    model = LoRAModel(
        name=request.name,
        base_model="Qwen/Qwen2.5-0.5B",
        lora_path=f"./output/lora/{int(time.time())}",
        dataset_id=request.dataset_id,
        industry_tag=request.industry_tag,
        lora_r=request.lora_r,
        lora_alpha=request.lora_alpha,
        status="training"
    )
    session.add(model)
    session.commit()

    # Start background training
    config = {
        "lora_r": request.lora_r,
        "lora_alpha": request.lora_alpha,
        "lora_dropout": request.lora_dropout,
        "num_train_epochs": request.num_train_epochs,
        "per_device_batch_size": request.per_device_batch_size,
        "learning_rate": request.learning_rate
    }

    background_tasks.add_task(run_training, request.dataset_id, model.id, config)

    return {
        "model_id": model.id,
        "status": "training started",
        "message": "Training started in background"
    }


@router.get("/status")
async def get_training_status():
    """Get current training status"""
    global _training_state, _training_callback

    elapsed = time.time() - _training_state["start_time"] if _training_state["start_time"] else 0

    # Calculate progress from callback
    progress = _training_state["progress"]
    current_step = _training_state["current_step"]

    if _training_callback and _training_callback.history["train_loss"]:
        train_loss = _training_callback.history["train_loss"][-1]
    else:
        train_loss = _training_state.get("train_loss")

    return TrainStatusResponse(
        status="running" if _training_state["is_running"] else "idle",
        progress=progress,
        current_step=current_step,
        total_steps=_training_state["total_steps"],
        train_loss=train_loss,
        eval_loss=_training_state.get("eval_loss"),
        elapsed_time=elapsed,
        eta=None
    )


@router.post("/stop")
async def stop_training():
    """Stop current training"""
    global _training_state

    if not _training_state["is_running"]:
        raise HTTPException(400, "No training in progress")

    _training_state["is_running"] = False

    return {"message": "Training stop requested"}


@router.get("/models")
async def list_models():
    """List all trained models"""
    session = get_session()
    models = session.query(LoRAModel).order_by(LoRAModel.created_at.desc()).all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "base_model": m.base_model,
            "lora_path": m.lora_path,
            "industry_tag": m.industry_tag,
            "status": m.status,
            "lora_r": m.lora_r,
            "train_loss": m.train_loss,
            "train_samples": m.train_samples,
            "training_time": m.training_time,
            "created_at": m.created_at.isoformat()
        }
        for m in models
    ]


@router.get("/{model_id}")
async def get_model(model_id: int):
    """Get model details"""
    session = get_session()
    model = session.query(LoRAModel).filter(LoRAModel.id == model_id).first()

    if not model:
        raise HTTPException(404, "Model not found")

    return {
        "id": model.id,
        "name": model.name,
        "base_model": model.base_model,
        "lora_path": model.lora_path,
        "merged_path": model.merged_path,
        "industry_tag": model.industry_tag,
        "status": model.status,
        "lora_r": model.lora_r,
        "lora_alpha": model.lora_alpha,
        "train_loss": model.train_loss,
        "train_samples": model.train_samples,
        "eval_samples": model.eval_samples,
        "training_time": model.training_time,
        "created_at": model.created_at.isoformat()
    }


@router.delete("/{model_id}")
async def delete_model(model_id: int):
    """Delete a model"""
    import shutil
    from pathlib import Path

    session = get_session()
    model = session.query(LoRAModel).filter(LoRAModel.id == model_id).first()

    if not model:
        raise HTTPException(404, "Model not found")

    # Delete files
    lora_path = Path(model.lora_path)
    if lora_path.exists():
        shutil.rmtree(lora_path)

    if model.merged_path:
        merged_path = Path(model.merged_path)
        if merged_path.exists():
            shutil.rmtree(merged_path)

    session.delete(model)
    session.commit()

    return {"message": "Model deleted", "id": model_id}
