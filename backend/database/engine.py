"""
Database engine configuration with backup support.
Uses SQLite by default, can be configured for PostgreSQL.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_DIR = Path(__file__).parent.parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)

BACKUP_DIR = DATABASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{DATABASE_DIR}/brains.db"
)

# Engine configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Enable WAL mode for better concurrent access and crash recovery
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other databases
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print(f"[DATABASE] Initialized at {DATABASE_URL}")


def create_backup(name: str = None) -> Path:
    """Create a backup of the database."""
    if not DATABASE_URL.startswith("sqlite"):
        raise NotImplementedError("Backup only supported for SQLite currently")
    
    db_path = DATABASE_DIR / "brains.db"
    if not db_path.exists():
        raise FileNotFoundError("Database file not found")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name}_{timestamp}" if name else timestamp
    backup_path = BACKUP_DIR / f"brains_backup_{backup_name}.db"
    
    # Copy with WAL checkpoint first
    with engine.connect() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    
    shutil.copy2(db_path, backup_path)
    print(f"[BACKUP] Created: {backup_path}")
    return backup_path


def restore_backup(backup_path: Path) -> bool:
    """Restore database from backup."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    
    db_path = DATABASE_DIR / "brains.db"
    
    # Close all connections
    engine.dispose()
    
    # Restore
    shutil.copy2(backup_path, db_path)
    print(f"[RESTORE] Restored from: {backup_path}")
    return True


def list_backups() -> list:
    """List available backups."""
    backups = []
    for f in BACKUP_DIR.glob("brains_backup_*.db"):
        stat = f.stat()
        backups.append({
            "name": f.name,
            "path": str(f),
            "size_mb": stat.st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    return sorted(backups, key=lambda x: x["created"], reverse=True)
