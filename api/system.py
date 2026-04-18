"""
FastAPI routes for System operations (auth, logs, settings)
"""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from api.database import User, OperationLog, init_db, get_default_db_path
from utils.hardware_detect import detect_hardware, get_gpu_info, get_cpu_info

router = APIRouter(prefix="/api/system", tags=["system"])

_engine, _Session = None, None

# Simple session management (single-user mode)
_active_session = {
    "token": None,
    "expires_at": None,
    "user_id": None
}


def get_session():
    global _engine, _Session
    if _Session is None:
        db_path = get_default_db_path()
        _engine, _Session = init_db(db_path)
    return _Session()


def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password"""
    return hash_password(password) == hashed


def create_session(user_id: int) -> str:
    """Create a new session"""
    import secrets
    token = secrets.token_hex(16)
    _active_session["token"] = token
    _active_session["user_id"] = user_id
    _active_session["expires_at"] = time.time() + 3600  # 1 hour
    return token


def verify_session(authorization: Optional[str] = Header(None)) -> bool:
    """Verify session token"""
    if not authorization:
        return False

    if not _active_session["token"]:
        return False

    if time.time() > _active_session["expires_at"]:
        _active_session["token"] = None
        return False

    if authorization != _active_session["token"]:
        return False

    return True


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class LogQuery(BaseModel):
    operation_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 50
    offset: int = 0


@router.post("/login")
async def login(request: LoginRequest):
    """Login to the system"""
    session = get_session()

    # For first-time setup, create default user
    user = session.query(User).first()
    if not user:
        user = User(
            username="admin",
            password_hash=hash_password("admin123")
        )
        session.add(user)
        session.commit()
        return {"message": "Default user created", "token": create_session(user.id)}

    # Verify credentials
    if user.username != request.username:
        raise HTTPException(401, "Invalid username or password")

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")

    token = create_session(user.id)

    return {
        "message": "Login successful",
        "token": token,
        "username": user.username
    }


@router.post("/logout")
async def logout():
    """Logout from the system"""
    _active_session["token"] = None
    return {"message": "Logged out"}


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user info"""
    if not verify_session(authorization):
        raise HTTPException(401, "Not authenticated")

    session = get_session()
    user = session.query(User).filter(User.id == _active_session["user_id"]).first()

    if not user:
        raise HTTPException(404, "User not found")

    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat()
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    authorization: Optional[str] = Header(None)
):
    """Change user password"""
    if not verify_session(authorization):
        raise HTTPException(401, "Not authenticated")

    session = get_session()
    user = session.query(User).filter(User.id == _active_session["user_id"]).first()

    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(400, "Incorrect old password")

    user.password_hash = hash_password(request.new_password)
    session.commit()

    return {"message": "Password changed successfully"}


@router.get("/logs")
async def get_logs(
    operation_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get operation logs"""
    session = get_session()

    query = session.query(OperationLog)

    if operation_type:
        query = query.filter(OperationLog.operation_type == operation_type)
    if status:
        query = query.filter(OperationLog.status == status)

    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "operation_type": log.operation_type,
                "operation_details": log.operation_details,
                "status": log.status,
                "error_message": log.error_message,
                "duration": log.duration,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }


@router.get("/logs/export")
async def export_logs(
    operation_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export logs to JSON file"""
    import json
    from pathlib import Path

    session = get_session()
    query = session.query(OperationLog)

    if operation_type:
        query = query.filter(OperationLog.operation_type == operation_type)

    logs = query.order_by(OperationLog.created_at.desc()).all()

    # Convert to serializable format
    log_list = [
        {
            "id": log.id,
            "operation_type": log.operation_type,
            "operation_details": log.operation_details,
            "status": log.status,
            "error_message": log.error_message,
            "duration": log.duration,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]

    # Save to file
    export_dir = Path("./data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = export_dir / f"logs_{timestamp}.json"

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(log_list, f, ensure_ascii=False, indent=2)

    return {
        "message": "Logs exported",
        "path": str(export_path),
        "count": len(log_list)
    }


@router.get("/hardware")
async def get_hardware_info():
    """Get hardware information"""
    mode = detect_hardware()

    if mode in ["GPU", "QLoRA"]:
        info = get_gpu_info()
    else:
        info = get_cpu_info()

    return {
        "mode": mode,
        "info": info
    }


@router.get("/settings")
async def get_settings():
    """Get system settings"""
    from api.database import get_default_db_path

    try:
        with open("config.yaml", "r") as f:
            import yaml
            config = yaml.safe_load(f)
    except:
        config = {}

    return {
        "db_path": get_default_db_path(),
        "config": config
    }
