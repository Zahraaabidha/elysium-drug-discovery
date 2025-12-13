from app.services.discovery import run_discovery
from app.db import get_db

def run_discovery_agent(target_id: str):
    """
    Agent goal:
    - Run molecule discovery
    - Rank results
    - Return best candidate + context
    """

    db = next(get_db())

    payload = {
        "target_id": target_id,
        "num_molecules": 10,
        "lipinski_only": True
    }

    result = run_discovery(payload, db)

    molecules = result.molecules

    if not molecules:
        return {
            "status": "no_results",
            "message": "No valid molecules generated"
        }

    # Agent decision: pick highest scoring molecule
    best = max(molecules, key=lambda m: m.score)

    return {
        "status": "success",
        "run_id": result.run_id,
        "target_id": target_id,
        "best_candidate": best,
        "all_candidates": molecules,
        "decision_policy": "max_score"
    }
