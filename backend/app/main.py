import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from . import models  # noqa: F401  # ensure models are imported
from .schemas import (
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryRunListResponse,
    DiscoveryRunSummary,
    TargetGraphResponse,
    DrugGraphResponse,
    Molecule as MoleculeSchema,
)
from .models import DiscoveryRun
from .services.discovery import run_discovery
from .similarity import find_combined_similar_drugs
from .services.kg import get_target_graph, get_drug_graph
from .services.kg_routes import router as kg_router

# --------------------------------------------------------------------
# API key authentication (simple header-based)
# --------------------------------------------------------------------
API_KEY = os.getenv("API_KEY", "changeme")  # 🔑 default matches frontend


def api_key_header(x_api_key: str = Header(..., alias="X-API-KEY")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


# --------------------------------------------------------------------
# FastAPI app setup
# --------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ELYSIUM – AI-Driven Drug Discovery Toolkit",
    version="0.1.0",
    description="Backend API for ELYSIUM, a modular agentic drug discovery system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include KG-related routes (e.g. /kg/init, etc. if you have them)
app.include_router(kg_router)


# --------------------------------------------------------------------
# Health
# --------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "elysium-backend"}


# --------------------------------------------------------------------
# Runs list
# --------------------------------------------------------------------
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


# --------------------------------------------------------------------
# Graph endpoints (SQL KG)
# --------------------------------------------------------------------
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


# --------------------------------------------------------------------
# Run detail (used by /runs/{id} page)
# --------------------------------------------------------------------
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
        if (
            semantic_neighbor is not None
            and semantic_neighbor.semantic_similarity is not None
        ):
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
                admet=None,  # you can later fetch ADMET from DB if stored
            )
        )

    return DiscoveryResponse(
        run_id=run.id,
        target_id=run.target_id,
        num_molecules=run.num_molecules,
        molecules=mol_objs,
    )


# --------------------------------------------------------------------
# Synchronous discovery endpoint (simple flow)
# --------------------------------------------------------------------
@app.post(
    "/discover",
    response_model=DiscoveryResponse,
    dependencies=[Depends(api_key_header)],
)
def discover_molecules(
    payload: DiscoveryRequest,
    db: Session = Depends(get_db),
):
    """
    Run the ELYSIUM discovery pipeline synchronously:
      - generate
      - score
      - similarity + ADMET
      - persist run & molecules
      - attach to KG (+ Arango/FAISS if available)
    """
    return run_discovery(payload, db)
