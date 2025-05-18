from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum
from .cluster import ClusterRead # Import ClusterRead from the new cluster schema file

class PriorityLevelEnum(str, enum.Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class DeploymentStatusEnum(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

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

class DeploymentDeleteRequest(BaseModel):
    cluster_id: int
