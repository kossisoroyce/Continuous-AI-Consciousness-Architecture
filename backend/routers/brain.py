"""
Brain management API router.
Handles brain CRUD, snapshots, backups, and events.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from database import get_db, BrainRepository, Brain, BrainSnapshot, BrainEvent, SessionLog
from database.engine import create_backup, list_backups, restore_backup
from sqlalchemy.orm import Session
from pathlib import Path

router = APIRouter(prefix="/brain", tags=["Brain Management"])


# ========== PYDANTIC MODELS ==========

class BrainCreate(BaseModel):
    id: str
    name: Optional[str] = None

class BrainResponse(BaseModel):
    id: str
    name: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    stability: float
    plasticity: float
    phase: str
    interaction_count: int
    trust_calibration: float
    overtrust_risk: float
    undertrust_risk: float
    
    class Config:
        from_attributes = True

class BrainStateUpdate(BaseModel):
    nurture_state: Optional[Dict[str, Any]] = None
    experience_state: Optional[Dict[str, Any]] = None
    hmt_state: Optional[Dict[str, Any]] = None
    create_snapshot: bool = False

class SnapshotResponse(BaseModel):
    id: int
    brain_id: str
    created_at: datetime
    snapshot_type: str
    description: Optional[str]
    stability: Optional[float]
    plasticity: Optional[float]
    phase: Optional[str]
    
    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    brain_id: str
    timestamp: datetime
    event_type: str
    severity: str
    description: Optional[str]
    stability_delta: Optional[float]
    plasticity_delta: Optional[float]
    
    class Config:
        from_attributes = True

class BackupInfo(BaseModel):
    name: str
    path: str
    size_mb: float
    created: str


# ========== BRAIN ENDPOINTS ==========

@router.post("/", response_model=BrainResponse)
def create_brain(brain: BrainCreate, db: Session = Depends(get_db)):
    """Create a new brain instance."""
    repo = BrainRepository(db)
    existing = repo.get(brain.id)
    if existing:
        raise HTTPException(status_code=400, detail="Brain already exists")
    
    new_brain = repo.create(brain.id, brain.name)
    return new_brain


@router.get("/", response_model=List[BrainResponse])
def list_brains(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all brains."""
    repo = BrainRepository(db)
    return repo.get_all(status=status)


@router.get("/{brain_id}", response_model=BrainResponse)
def get_brain(brain_id: str, db: Session = Depends(get_db)):
    """Get a brain by ID."""
    repo = BrainRepository(db)
    brain = repo.get(brain_id)
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")
    return brain


@router.get("/{brain_id}/full")
def get_brain_full(brain_id: str, db: Session = Depends(get_db)):
    """Get brain with full state data."""
    repo = BrainRepository(db)
    brain = repo.get(brain_id)
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")
    
    return {
        "id": brain.id,
        "name": brain.name,
        "status": brain.status,
        "created_at": brain.created_at.isoformat(),
        "updated_at": brain.updated_at.isoformat(),
        "metrics": {
            "stability": brain.stability,
            "plasticity": brain.plasticity,
            "phase": brain.phase,
            "interaction_count": brain.interaction_count,
            "trust_calibration": brain.trust_calibration,
            "overtrust_risk": brain.overtrust_risk,
            "undertrust_risk": brain.undertrust_risk
        },
        "nurture_state": brain.nurture_state,
        "experience_state": brain.experience_state,
        "hmt_state": brain.hmt_state
    }


@router.patch("/{brain_id}/state", response_model=BrainResponse)
def update_brain_state(brain_id: str, update: BrainStateUpdate, db: Session = Depends(get_db)):
    """Update brain state."""
    repo = BrainRepository(db)
    brain = repo.update_state(
        brain_id,
        nurture_state=update.nurture_state,
        experience_state=update.experience_state,
        hmt_state=update.hmt_state,
        create_snapshot=update.create_snapshot
    )
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")
    return brain


@router.post("/{brain_id}/archive", response_model=BrainResponse)
def archive_brain(brain_id: str, db: Session = Depends(get_db)):
    """Archive a brain (soft delete)."""
    repo = BrainRepository(db)
    brain = repo.archive(brain_id)
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")
    return brain


@router.delete("/{brain_id}")
def delete_brain(brain_id: str, db: Session = Depends(get_db)):
    """Permanently delete a brain."""
    repo = BrainRepository(db)
    if not repo.delete(brain_id):
        raise HTTPException(status_code=404, detail="Brain not found")
    return {"status": "deleted", "brain_id": brain_id}


# ========== SNAPSHOT ENDPOINTS ==========

@router.post("/{brain_id}/snapshot", response_model=SnapshotResponse)
def create_snapshot(brain_id: str, description: Optional[str] = None, db: Session = Depends(get_db)):
    """Create a manual snapshot."""
    repo = BrainRepository(db)
    snapshot = repo.create_snapshot(brain_id, description)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Brain not found")
    return snapshot


@router.get("/{brain_id}/snapshots", response_model=List[SnapshotResponse])
def list_snapshots(brain_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """List snapshots for a brain."""
    repo = BrainRepository(db)
    return repo.get_snapshots(brain_id, limit)


@router.post("/snapshot/{snapshot_id}/restore", response_model=BrainResponse)
def restore_from_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Restore brain to a snapshot."""
    repo = BrainRepository(db)
    brain = repo.restore_snapshot(snapshot_id)
    if not brain:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return brain


# ========== EVENT ENDPOINTS ==========

@router.get("/{brain_id}/events", response_model=List[EventResponse])
def list_events(
    brain_id: str, 
    limit: int = 50, 
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List events for a brain."""
    repo = BrainRepository(db)
    return repo.get_events(brain_id, limit, event_type)


# ========== BACKUP ENDPOINTS ==========

@router.post("/backup")
def create_database_backup(name: Optional[str] = None):
    """Create a full database backup."""
    try:
        backup_path = create_backup(name)
        return {"status": "created", "path": str(backup_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups", response_model=List[BackupInfo])
def get_backups():
    """List available backups."""
    return list_backups()


@router.post("/backup/restore")
def restore_database_backup(backup_name: str):
    """Restore from a backup file."""
    from database.engine import BACKUP_DIR
    backup_path = BACKUP_DIR / backup_name
    try:
        restore_backup(backup_path)
        return {"status": "restored", "from": backup_name}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
