from datetime import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    ForeignKey, CheckConstraint, Enum as SAEnum, Index
)
from sqlalchemy.orm import relationship
from .base import Base

class PriorityLevel(enum.Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class DeploymentStatus(enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Deployment(Base):
    __tablename__ = "deployments"
    id            = Column(Integer, primary_key=True)
    owner_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cluster_id    = Column(Integer, ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    image         = Column(String(255), nullable=False)  # Docker image (path or reference)
    required_cpu  = Column(Float, nullable=False)
    required_ram  = Column(Integer, nullable=False)
    required_gpu  = Column(Integer, nullable=False)
    priority      = Column(SAEnum(PriorityLevel, name="priority_level"), 
                           nullable=False, default=PriorityLevel.LOW)
    status        = Column(SAEnum(DeploymentStatus, name="deployment_status"), 
                           nullable=False, default=DeploymentStatus.QUEUED)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at    = Column(DateTime, nullable=True)
    finished_at   = Column(DateTime, nullable=True)
    retry_count   = Column(Integer, default=0, nullable=False)  # for tracking retries
    owner   = relationship("User", back_populates="deployments")
    cluster = relationship("Cluster", back_populates="deployments")

    __table_args__ = (
        CheckConstraint("required_cpu >= 0", name="ck_req_cpu_nonneg"),
        CheckConstraint("required_ram >= 0", name="ck_req_ram_nonneg"),
        CheckConstraint("required_gpu >= 0", name="ck_req_gpu_nonneg"),
        Index("ix_deploy_owner_id", "owner_id"),
        Index("ix_deploy_cluster_id", "cluster_id"),
        Index("ix_deploy_status", "status")
    )
