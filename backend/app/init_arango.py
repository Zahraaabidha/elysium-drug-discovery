# backend/app/init_arango.py
from .arangodb_client import get_arango_db

def init_arango_schema():
    db = get_arango_db()
    # vertex collections
    for name in ["targets", "drugs", "molecules", "diseases", "runs"]:
        if not db.has_collection(name):
            db.create_collection(name)
    # edge collections
    for name in ["binds", "treats", "similar_to", "generated_by"]:
        if not db.has_collection(name):
            db.create_collection(name, edge=True)
    print("Arango schema initialized.")

if __name__ == "__main__":
    init_arango_schema()
