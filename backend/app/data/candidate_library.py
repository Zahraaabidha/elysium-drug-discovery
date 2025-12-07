"""
Small library of drug-like molecules for ELYSIUM to sample from.

This is a stand-in for:
  - ChEMBL / ZINC subsets
  - or TamGen-generated libraries.

Each entry can have a name + SMILES; generation will mainly use SMILES.
"""

from typing import Dict, List

Candidate = Dict[str, str]

CANDIDATE_LIBRARY: List[Candidate] = [
    {
        "name": "Paracetamol",
        "smiles": "CC(=O)NC1=CC=C(O)C=C1",
    },
    {
        "name": "Ibuprofen",
        "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    },
    {
        "name": "Aspirin",
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
    },
    {
        "name": "Caffeine",
        "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C",
    },
    {
        "name": "Lidocaine",
        "smiles": "CCN(CC)CC(=O)N1CCN(CC1)C2=CC=CC=C2",
    },
    {
        "name": "Propranolol",
        "smiles": "CC(C)NCC(O)COC1=CC=CC2=CC=CC=C21",
    },
    {
        "name": "Metoprolol",
        "smiles": "CC(C)CCOC1=CC=C(C=C1)OCC(N)CO",
    },
    {
        "name": "Omeprazole",
        "smiles": "COC1=CC=C(C=C1OCC2=NC(=CS2)NC3=CC=CC(=N3)C)OC",
    },
    {
        "name": "Atorvastatin_fragment",
        "smiles": "CC(C)C1=CC(=O)CC(C1)CC(O)CC(O)CC(=O)O",
    },
    {
        "name": "Simple_alkyl_chain",
        "smiles": "CCCCCCO",
    },
    {
        "name": "Simple_amine",
        "smiles": "CCN(CC)CC",
    },
]
