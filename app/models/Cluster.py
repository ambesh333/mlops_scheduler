from datetime import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    ForeignKey, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .base import Base

class Cluster(Base):
    __tablename__ = "clusters"
    id            = Column(Integer, primary_key=True)
    name          = Column(String(100), nullable=False)
    owner_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    total_cpu     = Column(Float, nullable=False)  # total CPU units (e.g. cores or millicores)
    total_ram     = Column(Integer, nullable=False)  # total RAM (e.g. in MB)
    total_gpu     = Column(Integer, nullable=False)  # total number of GPUs
    available_cpu = Column(Float, nullable=False)
    available_ram = Column(Integer, nullable=False)
    available_gpu = Column(Integer, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    owner       = relationship("User", back_populates="clusters")
    organization = relationship("Organization", back_populates="clusters")
    deployments = relationship("Deployment", back_populates="cluster", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("available_cpu >= 0 AND available_cpu <= total_cpu", name="ck_cluster_cpu"),
        CheckConstraint("available_ram >= 0 AND available_ram <= total_ram", name="ck_cluster_ram"),
        CheckConstraint("available_gpu >= 0 AND available_gpu <= total_gpu", name="ck_cluster_gpu"),
        UniqueConstraint("owner_id", "name", name="uq_owner_cluster_name"),
        Index("ix_clusters_owner_id", "owner_id")
    )
