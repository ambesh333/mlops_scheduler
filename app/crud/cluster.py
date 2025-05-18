from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.Cluster import Cluster

async def create_cluster(db: AsyncSession, user_id: int, org_id: int, data):
    cluster = Cluster(
        name=data.name,
        owner_id=user_id,
        organization_id=org_id,
        total_cpu=data.total_cpu,
        total_ram=data.total_ram,
        total_gpu=data.total_gpu,
        available_cpu=data.total_cpu,
        available_ram=data.total_ram,
        available_gpu=data.total_gpu,
    )
    db.add(cluster)
    await db.commit()
    await db.refresh(cluster)
    return cluster


async def list_clusters(db: AsyncSession, current_user, org_id=None):
    query = select(Cluster).where(Cluster.owner_id == current_user.id)
    if org_id is not None:
        query = query.where(Cluster.organization_id == org_id)
    result = await db.execute(query)
    return result.scalars().all()

async def get_cluster(db: AsyncSession, current_user, cluster_id: int):
    result = await db.execute(select(Cluster).where(Cluster.id == cluster_id, Cluster.owner_id == current_user.id))
    cluster = result.scalars().first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found or not accessible")
    return cluster

async def delete_cluster(db: AsyncSession, current_user, cluster_id: int):
    result = await db.execute(select(Cluster).where(Cluster.id == cluster_id, Cluster.owner_id == current_user.id))
    cluster = result.scalars().first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found or not accessible")
    await db.delete(cluster)
    await db.commit()

async def get_cluster_status(db: AsyncSession, current_user, cluster_id: int):
    cluster = await get_cluster(db, current_user, cluster_id)
    return {"id": cluster.id, "name": cluster.name, "available_cpu": cluster.available_cpu, "available_ram": cluster.available_ram, "available_gpu": cluster.available_gpu}

async def list_cluster_deployments(db: AsyncSession, current_user, cluster_id: int):
    cluster = await get_cluster(db, current_user, cluster_id)
    return cluster.deployments