"""
Tiny demo library of known drugs for ELYSIUM similarity search.

In a real system this would come from DrugBank / ChEMBL / FDA datasets.
"""

from typing import List, Dict


DrugRecord = Dict[str, str]

FDA_LIKE_DRUGS: List[DrugRecord] = [
    {
        "name": "Paracetamol",
        "smiles": "CC(=O)NC1=CC=C(O)C=C1",
        "indication": "Pain relief, fever reduction",
    },
    {
        "name": "Ibuprofen",
        "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "indication": "Pain relief, anti-inflammatory",
    },
    {
        "name": "Aspirin",
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "indication": "Pain relief, anti-inflammatory, antiplatelet",
    },
    {
        "name": "Caffeine",
        "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C",
        "indication": "Stimulant",
    },
    {
        "name": "Lidocaine",
        "smiles": "CCN(CC)CC(=O)N1CCN(CC1)C2=CC=CC=C2",
        "indication": "Local anesthetic, antiarrhythmic",
    },
]
