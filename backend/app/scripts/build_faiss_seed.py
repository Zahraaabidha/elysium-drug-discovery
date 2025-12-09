# backend/scripts/build_faiss_seed.py
from app.fda_library import FDA_LIKE_DRUGS
from app.services.faiss_index import build_index
smiles = []
ids = []
for d in FDA_LIKE_DRUGS:
    s = d.get("smiles")
    if not s: continue
    smiles.append(s)
    # id tuple (collection, key)
    key = d.get("name", "").lower().replace(" ", "_")
    ids.append(("drugs", key))
print("Building index for", len(smiles), "drugs")
build_index(smiles, ids)
print("Built faiss index")
