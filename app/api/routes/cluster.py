from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.jwt import auth
from app.schemas.cluster_deploy import ClusterCreate, ClusterRead
from app.crud.cluster import (
    create_cluster,
    list_clusters,
    get_cluster,
    delete_cluster,
    get_cluster_status,
    list_cluster_deployments,
)
from app.crud.org import get_user_org_membership
from app.models.Role import RoleEnum
from typing import List

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

router = APIRouter()

@router.post("", response_model=ClusterRead, name="create_cluster")
async def create_cluster_endpoint(
    data: ClusterCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    org_id = getattr(data, 'organization_id', None)
    if org_id is None:
        raise HTTPException(status_code=400, detail="organization_id is required in the request body")
    membership = await get_user_org_membership(db, current_user.id, org_id)
    if not membership or membership.role != RoleEnum.Admin:
        raise HTTPException(status_code=403, detail="Only Admins can create clusters in this organization")
    return await create_cluster(db, current_user.id, org_id, data)

@router.get("", response_model=List[ClusterRead], name="list_clusters")
async def list_clusters_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    return await list_clusters(db, current_user)

@router.get("/{cluster_id}", response_model=ClusterRead, name="get_cluster")
async def get_cluster_endpoint(
    cluster_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    return await get_cluster(db, current_user, cluster_id)

@router.delete("/{cluster_id}", status_code=204, name="delete_cluster")
async def delete_cluster_endpoint(
    cluster_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    cluster = await get_cluster(db, current_user, cluster_id)
    org_id = cluster.organization_id
    membership = await get_user_org_membership(db, current_user.id, org_id)
    if not membership or membership.role != RoleEnum.Admin:
        raise HTTPException(status_code=403, detail="Only Admins can delete clusters in this organization")
    await delete_cluster(db, current_user, cluster_id)

@router.get("/{cluster_id}/status", name="get_cluster_status")
async def get_cluster_status_endpoint(
    cluster_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    return await get_cluster_status(db, current_user, cluster_id)

@router.get("/{cluster_id}/deployments", name="list_cluster_deployments")
async def list_cluster_deployments_endpoint(
    cluster_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    return await list_cluster_deployments(db, current_user, cluster_id)

