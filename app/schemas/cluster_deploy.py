from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

class PriorityLevelEnum(str, enum.Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class DeploymentStatusEnum(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# --- Cluster Schemas ---
class ClusterBase(BaseModel):
    name: str
    total_cpu: float
    total_ram: int
    total_gpu: int

class ClusterCreate(ClusterBase):
    organization_id: int

class ClusterRead(ClusterBase):
    id: int
    available_cpu: float
    available_ram: int
    available_gpu: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --- Deployment Schemas ---
class DeploymentBase(BaseModel):
    image: str
    required_cpu: float
    required_ram: int
    required_gpu: int
    priority: PriorityLevelEnum

class DeploymentCreate(DeploymentBase):
    cluster_id: int  

class DeploymentRead(DeploymentBase):
    id: int
    owner_id: int
    cluster_id: int
    status: DeploymentStatusEnum
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        orm_mode = True
