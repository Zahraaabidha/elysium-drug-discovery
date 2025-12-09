# backend/app/services/faiss_index.py

import faiss
import numpy as np
import os
from typing import List, Tuple
from filelock import FileLock
from .embeddings import embed_smiles

INDEX_PATH = "backend/faiss_index.index"
ID_MAP_PATH = "backend/faiss_id_map.npy"

# Global lock prevents concurrent writes
INDEX_LOCK = FileLock("backend/faiss_index.lock")


def load_index():
    if not os.path.exists(INDEX_PATH):
        return None, None
    index = faiss.read_index(INDEX_PATH)
    id_map = np.load(ID_MAP_PATH, allow_pickle=True)
    return index, id_map


def build_index(smiles_list: List[str], id_list: List[Tuple[str, str]]):
    """Build new FAISS index from scratch."""
    xb = embed_smiles(smiles_list).astype("float32")
    dim = xb.shape[1]

    with INDEX_LOCK:
        index = faiss.IndexFlatIP(dim)
        index.add(xb)

        faiss.write_index(index, INDEX_PATH)
        np.save(ID_MAP_PATH, np.array(id_list, dtype=object))

    return index


def add_to_index(smiles_list: List[str], id_list: List[Tuple[str, str]]):
    """Append vectors to FAISS index."""
    xb = embed_smiles(smiles_list).astype("float32")

    with INDEX_LOCK:
        index, id_map = load_index()

        # If index does not exist yet, build it
        if index is None:
            return build_index(smiles_list, id_list)

        # Check embedding dimension matches index dimension
        if xb.shape[1] != index.d:
            raise ValueError(f"FAISS dimension mismatch: {xb.shape[1]} vs {index.d}")

        # Append vectors
        index.add(xb)

        # Extend id map
        id_map = np.concatenate([id_map, np.array(id_list, dtype=object)])

        # Save back
        faiss.write_index(index, INDEX_PATH)
        np.save(ID_MAP_PATH, id_map)

    return index


def query_index(smiles: str, k: int = 5):
    """Return top-k semantic neighbors for a SMILES."""
    vec = embed_smiles([smiles]).astype("float32")

    with INDEX_LOCK:
        index, id_map = load_index()
        if index is None:
            return []

        D, I = index.search(vec, k)

    results = []
    for j, i in enumerate(I[0]):
        if i < 0:
            continue
        results.append({
            "id": tuple(id_map[i]),
            "score": float(D[0][j])
        })

    return results
