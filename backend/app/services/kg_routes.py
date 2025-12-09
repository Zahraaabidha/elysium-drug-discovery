# backend/app/services/kg_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from ..db import get_db
from .kg import get_target_graph, get_drug_graph

router = APIRouter(prefix="/graph", tags=["kg"])

@router.get("/target/{target_id}", response_model=Any)
def graph_target(target_id: str, db: Session = Depends(get_db)):
    """
    Return the target graph view (TargetGraphResponse) for a given target_id.
    """
    resp = get_target_graph(db, target_id)
    # If empty molecules and target node not found we still return the empty response
    return resp

@router.get("/drug/{drug_name}", response_model=Any)
def graph_drug(drug_name: str, db: Session = Depends(get_db)):
    """
    Return the drug graph view (DrugGraphResponse) for a given drug name.
    """
    resp = get_drug_graph(db, drug_name)
    return resp
