from typing import List
import logging

from sqlalchemy.orm import Session

from ..arangodb_client import get_arango_db
from ..schemas import Molecule, DiscoveryRequest, DiscoveryResponse, SimilarDrug
from ..core.config import resolve_target_sequence
from ..models import DiscoveryRun, MoleculeRecord
from ..similarity import find_combined_similar_drugs
from .scoring import get_scorer
from .generation import get_generator
from .kg import attach_run_to_kg
from .admet import calculate_admet
from .faiss_index import add_to_index, query_index

scorer = get_scorer()
generator = get_generator()


def run_discovery(req: DiscoveryRequest, db: Session) -> DiscoveryResponse:
    """
    ELYSIUM discovery pipeline (synchronous):

    1. Generate candidate molecules.
    2. Resolve target sequence.
    3. Score molecules with configured backend.
    4. Compute similarity to known drugs + ADMET.
    5. Optional Lipinski filter.
    6. Persist run & molecules in SQL.
    7. Attach to SQL KG.
    8. Best effort: write to Arango + FAISS.
    """

    # 1) Generate candidate molecules (via generator abstraction)
    smiles_list = generator.generate(req.target_id, req.num_molecules)

    # 2) Resolve target sequence
    target_seq = resolve_target_sequence(req.target_id)

    # 3) Score with configured backend
    scores = scorer.score(smiles_list, target_seq, req.target_id)

    # 4) Build Molecule objects with similarity + ADMET
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

    # 5) Optional Lipinski filter
    if req.lipinski_only:
        filtered = [
            m for m in molecules
            if m.admet is not None and m.admet.lipinski_pass
        ]
        if filtered:
            molecules = filtered

    # Sort by score desc
    molecules.sort(key=lambda m: m.score, reverse=True)

    # 6) Persist run & molecules in SQL
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

    # 7) Attach this run to the SQL knowledge graph
    attach_run_to_kg(db, run_record, molecules)

    db.commit()
    db.refresh(run_record)

    # From here on, Arango + FAISS are "best effort":
    # failures are logged but do not break the API.

    # 8a) Write to ArangoDB knowledge graph (if configured)
    try:
        arango = get_arango_db()
        mol_col = arango.collection("molecules")
        binds_col = arango.collection("binds")
        similar_col = arango.collection("similar_to")
        runs_col = arango.collection("runs")

        run_key = str(run_record.id)

        if not runs_col.has(run_key):
            runs_col.insert(
                {
                    "_key": run_key,
                    "target_id": run_record.target_id,
                    "num_molecules": int(run_record.num_molecules),
                }
            )

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

            if not mol_col.has(mol_key):
                mol_col.insert(mol_doc)

            # binds edge
            try:
                binds_col.insert(
                    {
                        "_from": f"molecules/{mol_key}",
                        "_to": f"targets/{req.target_id}",
                        "score": float(m.score),
                        "source": "ELYSIUM",
                    }
                )
            except Exception:
                # ignore duplicate or missing-target errors
                pass

            # similar_to edge: molecule -> known drug
            if m.similar_drug:
                drug_key = m.similar_drug.name.lower().replace(" ", "_")
                if (
                    arango.has_collection("drugs")
                    and arango.collection("drugs").has(drug_key)
                ):
                    try:
                        similar_col.insert(
                            {
                                "_from": f"molecules/{mol_key}",
                                "_to": f"drugs/{drug_key}",
                                "tanimoto": float(getattr(m.similar_drug, "similarity", 0.0) or 0.0),
                                "semantic": float(
                                    getattr(m.similar_drug, "semantic_similarity", 0.0)
                                    or 0.0
                                ),
                            }
                        )
                    except Exception:
                        pass

    except Exception as e:
        logging.exception("Failed to write to Arango KG: %s", e)

    # 8b) FAISS: query existing neighbors, then add these molecules
    try:
        # First: for each molecule, query semantic neighbors already in the index
        arango = None
        try:
            arango = get_arango_db()
            similar_col = arango.collection("similar_to")
        except Exception:
            similar_col = None

        run_key = str(run_record.id)

        for idx, m in enumerate(molecules):
            try:
                neighs = query_index(m.smiles, k=5)
            except Exception:
                continue

            sem_neighbor = None
            for item in neighs:
                coll, key = item["id"]
                if coll == "drugs":
                    sem_neighbor = {
                        "name": key,
                        "semantic_similarity": item["score"],
                    }
                    break

            if sem_neighbor:
                # attach semantic neighbor into Molecule object (for response)
                m.similar_drug_semantic = SimilarDrug(
                    name=sem_neighbor["name"],
                    smiles="",
                    indication=None,
                    similarity=0.0,
                    semantic_similarity=float(
                        sem_neighbor["semantic_similarity"]
                    ),
                )

                # optionally create an Arango edge
                if similar_col is not None:
                    try:
                        similar_col.insert(
                            {
                                "_from": f"molecules/{run_key}_{idx}",
                                "_to": f"drugs/{sem_neighbor['name']}",
                                "semantic": float(
                                    sem_neighbor["semantic_similarity"]
                                ),
                            }
                        )
                    except Exception:
                        pass

        # Then: add all new molecules to the FAISS index
        try:
            new_smiles = [m.smiles for m in molecules]
            new_ids = [("molecules", f"{run_key}_{i}") for i in range(len(molecules))]
            add_to_index(new_smiles, new_ids)
        except Exception as e:
            logging.exception("Faiss add failed: %s", e)

    except Exception:
        logging.exception("Faiss orchestration failed.")

    # 9) Return response
    return DiscoveryResponse(
        run_id=run_record.id,
        target_id=run_record.target_id,
        num_molecules=run_record.num_molecules,
        molecules=molecules,
    )
