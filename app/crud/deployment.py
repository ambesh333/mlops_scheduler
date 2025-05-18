# app/crud/deployment.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.Cluster import Cluster
from app.models.Deployment import Deployment
from app.schemas.deployment import DeploymentCreate
from datetime import datetime
from app.models.UserOrganizations import UserOrganization
from sqlalchemy import and_
from app.core.redis_client import push_deployment_to_queue
from app.models.Deployment import DeploymentStatus

async def create_deployment(
    db: AsyncSession,
    user_id: int,
    org_id: int,
    cluster_id: int,
    data: DeploymentCreate
) -> Deployment:

    cluster = await db.get(Cluster, cluster_id)
    if not cluster or cluster.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Cluster not found or not in this organization")

    if (cluster.available_cpu < data.required_cpu or
        cluster.available_ram < data.required_ram or
        cluster.available_gpu < data.required_gpu):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient cluster resources. Required: CPU={data.required_cpu}, RAM={data.required_ram}, GPU={data.required_gpu}. Available: CPU={cluster.available_cpu}/{cluster.total_cpu}, RAM={cluster.available_ram}/{cluster.total_ram}, GPU={cluster.available_gpu}/{cluster.total_gpu}."
        )

    cluster.available_cpu -= data.required_cpu
    cluster.available_ram -= data.required_ram
    cluster.available_gpu -= data.required_gpu

    dep = Deployment(
        owner_id=user_id,
        cluster_id=cluster_id,
        image=data.image,
        required_cpu=data.required_cpu,
        required_ram=data.required_ram,
        required_gpu=data.required_gpu,
        priority=data.priority,
        status="QUEUED",  
        created_at=datetime.utcnow()
    )
    db.add(dep)
    await db.commit()
    await db.refresh(dep)
    push_deployment_to_queue({
    "deployment_id": dep.id,
    "priority": dep.priority.value,
    "required_cpu": dep.required_cpu,
    "required_ram": dep.required_ram,
    "required_gpu": dep.required_gpu,
    "cluster_id": dep.cluster_id
    })
    return dep

async def list_deployments(
    db: AsyncSession,
    user_id: int,
    org_id: int,
    cluster_id: int
):
    cluster = await db.get(Cluster, cluster_id)
    if not cluster or cluster.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Cluster not found or not in this organization")
    result = await db.execute(
        select(Deployment)
        .where(Deployment.cluster_id == cluster_id)
    )
    return result.scalars().all()

async def get_deployment(
    db: AsyncSession,
    user_id: int,
    deployment_id: int
) -> Deployment:
    result = await db.execute(
        select(Deployment)
        .where(Deployment.id == deployment_id)
    )
    dep = result.scalars().first()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")

    cluster = await db.get(Cluster, dep.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Associated cluster not found")

    if dep.owner_id == user_id:
        return dep

    result = await db.execute(
        select(UserOrganization).where(
            and_(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == cluster.organization_id
            )
        )
    )
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")

    return dep

async def delete_deployment(
    db: AsyncSession,
    deployment_id: int
):
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    dep = result.scalars().first()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")

    await db.delete(dep)
    await db.commit()

async def get_deployment_by_id_for_scheduling(
    db: AsyncSession,
    deployment_id: int
) -> Deployment | None:
    """Fetches a deployment by ID for scheduling purposes (no user/org checks)."""
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    return result.scalars().first()

async def list_running_deployments_for_cluster(
    db: AsyncSession,
    cluster_id: int
) -> list[Deployment]:
    """Lists running deployments for a specific cluster."""
    result = await db.execute(
        select(Deployment)
        .where(Deployment.cluster_id == cluster_id)
        .where(Deployment.status == DeploymentStatus.RUNNING)
    )
    return result.scalars().all()
