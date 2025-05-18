# app/core/scheduler_db.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.Deployment import Deployment
from app.models.Cluster import Cluster
from app.models.Deployment import DeploymentStatus
from app.core.database import AsyncSessionLocal
from typing import List, Dict

async def fetch_running_deployments_from_db():
    """Fetches all currently running deployments."""
    running_jobs = []
    async with AsyncSessionLocal() as session: 
        result = await session.execute(
            select(Deployment).where(Deployment.status == DeploymentStatus.RUNNING)
        )
        deployments = result.scalars().all()

        for dep in deployments:
            running_jobs.append({
                'id': dep.id,
                'priority': dep.priority.value,
                'cpu': dep.required_cpu,
                'ram': dep.required_ram,
                'gpu': dep.required_gpu,
                'cluster_id': dep.cluster_id
            })
    return running_jobs

async def fetch_all_cluster_resources_from_db():
    """Fetches resources for all clusters."""
    cluster_resources = {}
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Cluster))
        clusters = result.scalars().all()
        for cluster in clusters:
             cluster_resources[cluster.id] = {
                'cluster_id': cluster.id,
                'total_cpu': cluster.total_cpu,
                'total_ram': cluster.total_ram,
                'total_gpu': cluster.total_gpu,
                'available_cpu': cluster.available_cpu,
                'available_ram': cluster.available_ram,
                'available_gpu': cluster.available_gpu
            }
    return cluster_resources 


async def mark_jobs_running(cluster_id: int, job_ids: List[int]) -> None:
    """
    For each deployment ID in job_ids:
    - set status=RUNNING
    - subtract its resources from the cluster's available_* fields
    """
    async with AsyncSessionLocal() as session:
        cluster = await session.get(Cluster, cluster_id, with_for_update=True)
        if not cluster:
            raise RuntimeError(f"Cluster {cluster_id} not found in DB")

        result = await session.execute(
            select(Deployment).where(Deployment.id.in_(job_ids))
        )
        deployments = result.scalars().all()

        for dep in deployments:
            if dep.status != DeploymentStatus.RUNNING:
                cluster.available_cpu -= dep.required_cpu
                cluster.available_ram -= dep.required_ram
                cluster.available_gpu -= dep.required_gpu
                dep.status = DeploymentStatus.RUNNING

        await session.commit()


async def requeue_jobs(cluster_id: int, job_ids: List[int]) -> None:
    """
    For each deployment ID in job_ids that was previously RUNNING:
    - set status=QUEUED
    - add its resources back to the cluster's available_* fields
    """
    async with AsyncSessionLocal() as session:
        cluster = await session.get(Cluster, cluster_id, with_for_update=True)
        if not cluster:
            raise RuntimeError(f"Cluster {cluster_id} not found in DB")

        result = await session.execute(
            select(Deployment).where(Deployment.id.in_(job_ids))
        )
        deployments = result.scalars().all()

        for dep in deployments:
            if dep.status == DeploymentStatus.RUNNING:
                cluster.available_cpu += dep.required_cpu
                cluster.available_ram += dep.required_ram
                cluster.available_gpu += dep.required_gpu
                dep.status = DeploymentStatus.QUEUED

        await session.commit()