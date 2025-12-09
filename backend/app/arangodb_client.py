# backend/app/arangodb_client.py
import os
from arango import ArangoClient

ARANGO_URL = os.getenv("ARANGO_URL", "http://127.0.0.1:8529")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "")
ARANGO_DB_NAME = os.getenv("ARANGO_DB_NAME", "elysium_kg")

def get_arango_db(create_if_missing=True):
    client = ArangoClient(hosts=ARANGO_URL)
    sys_db = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if create_if_missing and not sys_db.has_database(ARANGO_DB_NAME):
        sys_db.create_database(ARANGO_DB_NAME)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    return db
