# backend/app/kg_seed.py
from .arangodb_client import get_arango_db

def upsert(collection, key, doc):
    if collection.has(key):
        collection.update({"_key": key, **doc})
    else:
        collection.insert({"_key": key, **doc})

def seed():
    db = get_arango_db()
    targets = db.collection("targets")
    drugs = db.collection("drugs")
    binds = db.collection("binds")
    diseases = db.collection("diseases")

    upsert(targets, "EGFR", {
        "symbol": "EGFR",
        "uniprot_id": "P00533",
        "name": "Epidermal growth factor receptor"
    })

    upsert(drugs, "ibuprofen", {
        "name": "Ibuprofen",
        "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "indication": "Pain relief, anti-inflammatory"
    })
    upsert(drugs, "paracetamol", {
        "name": "Paracetamol",
        "smiles": "CC(=O)NC1=CC=C(O)C=C1",
        "indication": "Pain relief, fever reduction"
    })

    binds.insert({"_from": "drugs/ibuprofen", "_to": "targets/EGFR", "evidence": "seed"})
    binds.insert({"_from": "drugs/paracetamol", "_to": "targets/EGFR", "evidence": "seed"})

    print("Seed complete.")

if __name__ == "__main__":
    seed()
