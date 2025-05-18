# app/crud/deployment.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.Cluster import Cluster
from app.models.Deployment import Deployment
from app.schemas.deployment import DeploymentCreate
from datetime import datetime
from app.crud.org import get_user_org_membership
from app.models.Role import RoleEnum
from app.models.UserOrganizations import UserOrganization
from sqlalchemy import and_

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
            detail="Insufficient cluster resources"
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
