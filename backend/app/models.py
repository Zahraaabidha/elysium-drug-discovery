import uuid
import datetime as dt

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    String,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base

def gen_uuid():
    return str(uuid.uuid4())

class DiscoveryRun(Base):
    __tablename__ = "discovery_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    target_id = Column(String, nullable=False)
    num_molecules = Column(Integer, nullable=False, default=0)

    # status/progress fields (if present in your schema)
    status = Column(String, nullable=False, default="queued")
    progress = Column(Float, nullable=False, default=0.0)
    cancelled = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ====== THIS is the expected property name: 'molecules' ======
    molecules = relationship(
        "MoleculeRecord",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

class MoleculeRecord(Base):
    __tablename__ = "molecules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("discovery_runs.id"), nullable=False)
    smiles = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ====== THIS must match the DiscoveryRun relationship back_populates ======
    run = relationship("DiscoveryRun", back_populates="molecules")


class KGNode(Base):
    __tablename__ = "kg_nodes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_type = Column(String, index=True)  # 'drug', 'target', 'generated_molecule', etc.
    external_id = Column(String, index=True, nullable=True)  # e.g. 'EGFR', 'runid:0'
    name = Column(String, index=True, nullable=False)
    smiles = Column(String, nullable=True)
    info = Column(Text, nullable=True)

    outgoing_edges = relationship(
        "KGEdge",
        back_populates="source",
        foreign_keys="KGEdge.source_id",
    )
    incoming_edges = relationship(
        "KGEdge",
        back_populates="target",
        foreign_keys="KGEdge.target_id",
    )


class KGEdge(Base):
    __tablename__ = "kg_edges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("kg_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("kg_nodes.id"), nullable=False)
    relation = Column(String, index=True)  # 'SIMILAR_TO', 'BINDS', 'TREATS'
    weight = Column(Float, nullable=True)  # e.g. similarity or score
    extra = Column(Text, nullable=True)    # JSON/string with extra info

    source = relationship(
        "KGNode",
        foreign_keys=[source_id],
        back_populates="outgoing_edges",
    )
    target = relationship(
        "KGNode",
        foreign_keys=[target_id],
        back_populates="incoming_edges",
    )
