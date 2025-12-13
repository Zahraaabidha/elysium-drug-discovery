from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .arangodb_client import get_arango_db
from fastapi import APIRouter

from .schemas import (
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryRunListResponse,
    DiscoveryRunSummary,
    Molecule as MoleculeSchema,
    TargetGraphResponse, 
    DrugGraphResponse,      # <-- add this
)
from .models import DiscoveryRun
from .services.discovery import run_discovery
from .db import Base, engine, get_db
from . import models  # ensure models are imported so metadata knows them
from .similarity import find_combined_similar_drugs
from .services.kg import get_target_graph, get_drug_graph
from app.routes.molecule_image import router as molecule_image_router
from app.agents.discovery_agent import run_discovery_agent

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ELYSIUM – AI-Driven Drug Discovery Toolkit",
    version="0.1.0",
    description="Backend API for ELYSIUM, a modular agentic drug discovery system."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(molecule_image_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "elysium-backend"}

@app.get("/runs", response_model=DiscoveryRunListResponse)
def list_runs(db: Session = Depends(get_db)):
    runs = (
        db.query(DiscoveryRun)
        .order_by(DiscoveryRun.created_at.desc())
        .limit(50)
        .all()
    )

    summaries = [
        DiscoveryRunSummary(
            run_id=run.id,
            target_id=run.target_id,
            num_molecules=run.num_molecules,
            created_at=run.created_at,
        )
        for run in runs
    ]

    return DiscoveryRunListResponse(runs=summaries)

@app.get("/graph/target/{target_id}", response_model=TargetGraphResponse)
def graph_for_target(target_id: str, db: Session = Depends(get_db)):
    """
    Graph view: all generated molecules for a given target,
    along with their closest known drug (if available).
    """
    return get_target_graph(db, target_id)


@app.get("/graph/drug/{drug_name}", response_model=DrugGraphResponse)
def graph_for_drug(drug_name: str, db: Session = Depends(get_db)):
    """
    Graph view: all generated molecules across all targets
    that are similar to a given known drug.
    """
    return get_drug_graph(db, drug_name)


@app.get("/runs/{run_id}", response_model=DiscoveryResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    mol_objs = []
    for m in sorted(run.molecules, key=lambda m: m.score, reverse=True):
        fp_neighbor, semantic_neighbor = find_combined_similar_drugs(m.smiles)

        note_parts = [m.notes or ""]
        if fp_neighbor is not None and fp_neighbor.similarity is not None:
            note_parts.append(
                f"(FP neighbor: {fp_neighbor.name}, Tanimoto={fp_neighbor.similarity:.2f})"
            )
        if semantic_neighbor is not None and semantic_neighbor.semantic_similarity is not None:
            note_parts.append(
                f"(chemBERTa neighbor: {semantic_neighbor.name}, "
                f"cosine={semantic_neighbor.semantic_similarity:.2f})"
            )

        mol_objs.append(
            MoleculeSchema(
                smiles=m.smiles,
                score=m.score,
                source=m.source,
                notes=" ".join(note_parts).strip(),
                similar_drug=fp_neighbor,
                similar_drug_semantic=semantic_neighbor,
            )
        )

    return DiscoveryResponse(
        run_id=run.id,
        target_id=run.target_id,
        num_molecules=run.num_molecules,
        molecules=mol_objs,
    )

@app.post("/discover", response_model=DiscoveryResponse)
def discover_molecules(
    payload: DiscoveryRequest,
    db: Session = Depends(get_db),
):
    return run_discovery(payload, db)

@app.post("/agent/discover")
def agent_discover(target_id: str):
    return run_discovery_agent(target_id)