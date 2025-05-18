from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

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
