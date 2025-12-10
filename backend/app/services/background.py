# backend/app/services/background.py
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import DiscoveryRun
from ..services.discovery import run_discovery  # your existing function
from ..schemas import DiscoveryRequest
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_discovery_background(run_id: str, payload_dict: Dict[str, Any]) -> None:
    """
    Background worker wrapper that runs the discovery pipeline for run_id.
    Updates DiscoveryRun.status / progress / error_message in DB.
    """
    db: Session = SessionLocal()
    try:
        # load run
        run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
        if run is None:
            logger.error("Run id not found: %s", run_id)
            return

        # mark as running
        run.status = "running"
        run.started_at = datetime.utcnow()
        run.attempts = (run.attempts or 0) + 1
        db.commit()

        # Convert payload to DiscoveryRequest-like if needed
        payload = DiscoveryRequest(**payload_dict)

        # Optionally: small checkpoints where we check cancel flag
        if run.cancelled:
            run.status = "cancelled"
            db.commit()
            return

        # Run the heavy job (this may write to DB / Arango / Faiss)
        # run_discovery currently returns a DiscoveryResponse; it's synchronous.
        # You may want to modify run_discovery to take a DB session or create a new one inside.
        try:
            result = run_discovery(payload, db)  # IMPORTANT: run_discovery uses SQLAlchemy session
            # done: update status
            run.status = "done"
            run.progress = 100.0
            run.finished_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            # mark failed
            db.rollback()
            run.error_message = str(e)
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            db.commit()
            logger.exception("Discovery run failed: %s", e)
    finally:
        db.close()
