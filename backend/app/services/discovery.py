import uuid
from typing import List

from sqlalchemy.orm import Session

from ..arangodb_client import get_arango_db
from ..schemas import Molecule, DiscoveryRequest, DiscoveryResponse
from ..core.config import resolve_target_sequence
from ..models import DiscoveryRun, MoleculeRecord
from ..similarity import find_combined_similar_drugs
from .scoring import get_scorer
from .generation import get_generator
from .kg import attach_run_to_kg
from .admet import calculate_admet


scorer = get_scorer()
generator = get_generator()

def _generate_candidate_smiles(num: int) -> List[str]:
    """
    Temporary candidate generator.

    Right now we just cycle through a few simple SMILES strings.
    Later this will be replaced by:
      - TamGen or other Transformer generator
      - Library-based sampling + scaffold hopping
    """
    base_smiles = [
        "CCO",          # ethanol
        "CC(=O)O",      # acetic acid
        "CCN(CC)CC",    # triethylamine
        "CCOC(=O)C",    # ethyl acetate
        "CC(C)O",       # isopropanol
    ]
    return (base_smiles * ((num // len(base_smiles)) + 1))[:num]


def _simple_score(smiles_list: List[str], target_sequence: str, target_id: str) -> List[float]:
    """
    Simple deterministic scoring stub.

    This mimics a DTI model by assigning decreasing scores.
    It keeps ELYSIUM's pipeline structure intact until we plug in
    DeepPurpose (or another real model) again.
    """
    scores: List[float] = []
    base = 1.0
    step = 0.05  # how much the score drops per molecule

    for i, _ in enumerate(smiles_list):
        s = base - step * i
        if s < 0:
            s = 0.0
        scores.append(s)

    return scores


def run_discovery(req: DiscoveryRequest, db: Session) -> DiscoveryResponse:
    """
    ELYSIUM discovery pipeline:

    1. Generate candidate molecules.
    2. Resolve target sequence.
    3. Score molecules with configured backend (stub or DeepPurpose).
    4. Compute similarity to known drugs.
    5. Save to DB.
    6. Return ranked molecules.
    """

    # 1) Generate candidate molecules (library-based for now)
    smiles_list = generator.generate(req.target_id, req.num_molecules)


    # 2) Resolve target sequence
    target_seq = resolve_target_sequence(req.target_id)

    # 3) Score with configured backend
    scores = scorer.score(smiles_list, target_seq, req.target_id)

    # 4) Build Molecule objects with similarity info
    molecules: List[Molecule] = []
    for smi, score in zip(smiles_list, scores):
        fp_neighbor, semantic_neighbor = find_combined_similar_drugs(smi)
        admet_props = calculate_admet(smi)

        note_parts = ["Scored with ELYSIUM backend."]

        if fp_neighbor is not None:
            note_parts.append(
                f"Most similar known drug (fingerprint): "
                f"{fp_neighbor.name} (Tanimoto={fp_neighbor.similarity:.2f})."
            )

        if (
            semantic_neighbor is not None
            and semantic_neighbor.semantic_similarity is not None
        ):
            note_parts.append(
                f"Most similar known drug (chemBERTa): "
                f"{semantic_neighbor.name} "
                f"(cosine={semantic_neighbor.semantic_similarity:.2f})."
            )

        if admet_props is not None:
            note_parts.append(
                f"Lipinski pass={admet_props.lipinski_pass}, "
                f"violations={admet_props.lipinski_violations}."
            )

        molecules.append(
            Molecule(
                smiles=smi,
                score=score,
                source=type(scorer).__name__,
                notes=" ".join(note_parts),
                similar_drug=fp_neighbor,
                similar_drug_semantic=semantic_neighbor,
                admet=admet_props,
            )
        )

            # Optional Lipinski filter
    if req.lipinski_only:
        filtered = [
            m for m in molecules
            if m.admet is not None and m.admet.lipinski_pass
        ]
        if filtered:
            molecules = filtered
        # if filtered is empty, we keep original list, so the user still gets something


    # Sort by score desc
    molecules.sort(key=lambda m: m.score, reverse=True)

    # 5) Save to DB (same as before)
    run_record = DiscoveryRun(
        target_id=req.target_id,
        num_molecules=len(molecules),
    )
    db.add(run_record)
    db.flush()  # assign ID

    for m in molecules:
        db.add(
            MoleculeRecord(
                run_id=run_record.id,
                smiles=m.smiles,
                score=m.score,
                source=m.source,
                notes=m.notes,
            )
        )

    # Attach this run to the knowledge graph (nodes + edges)
    attach_run_to_kg(db, run_record, molecules)

    db.commit()
    db.refresh(run_record)

    # --- Write to Arango (KG) ---
    try:
        arango = get_arango_db()  # uses env vars from arangodb_client.py
        mol_col = arango.collection("molecules")
        binds_col = arango.collection("binds")
        similar_col = arango.collection("similar_to")
        runs_col = arango.collection("runs")

        # upsert run metadata into runs collection
        run_key = str(run_record.id)
        if not runs_col.has(run_key):
            runs_col.insert({
                "_key": run_key,
                "target_id": run_record.target_id,
                "num_molecules": int(run_record.num_molecules),
            })

        # write molecules and edges
        for idx, m in enumerate(molecules):
            mol_key = f"{run_key}_{idx}"
            mol_doc = {
                "_key": mol_key,
                "run_id": run_key,
                "index": int(idx),
                "target_id": req.target_id,
                "smiles": m.smiles,
                "score": float(m.score),
            }

            # insert molecule document if missing
            if not mol_col.has(mol_key):
                mol_col.insert(mol_doc)

            # binds edge: molecule -> target (target collection expected to have doc with _key=req.target_id)
            try:
                binds_col.insert({
                    "_from": f"molecules/{mol_key}",
                    "_to": f"targets/{req.target_id}",
                    "score": float(m.score),
                    "source": "ELYSIUM"
                })
            except Exception:
                # if it already exists or target missing, ignore to avoid crash
                pass

            # similar_to edge: molecule -> known drug (if found)
            if m.similar_drug:
                # normalize drug key to match seed script: lowercase, underscores, strip spaces
                drug_key = m.similar_drug.name.lower().replace(" ", "_")
                # ensure drugs collection and document exists
                if arango.has_collection("drugs") and arango.collection("drugs").has(drug_key):
                    try:
                        similar_col.insert({
                            "_from": f"molecules/{mol_key}",
                            "_to": f"drugs/{drug_key}",
                            "tanimoto": float(getattr(m.similar_drug, "similarity", 0.0) or 0.0),
                            "semantic": float(getattr(m.similar_drug, "semantic_similarity", 0.0) or 0.0),
                        })
                    except Exception:
                        # ignore insert errors (duplicates, etc.)
                        pass

    except Exception as e:
        # do not break discovery run if Arango is down; just log
        import logging
        logging.exception("Failed to write to Arango KG: %s", e)

         

    # 6) Return response
    return DiscoveryResponse(
        run_id=run_record.id,
        target_id=run_record.target_id,
        num_molecules=run_record.num_molecules,
        molecules=molecules,
    )
