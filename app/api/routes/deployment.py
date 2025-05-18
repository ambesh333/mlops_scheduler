# app/api/routes/deployment.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List

from app.core.database import AsyncSessionLocal
from app.core.jwt import auth
from app.models.Role import RoleEnum
from app.schemas.deployment import DeploymentCreate, DeploymentRead, DeploymentDeleteRequest
from app.crud.deployment import (
    create_deployment,
    list_deployments,
    get_deployment as get_deployment_crud,
    delete_deployment as delete_deployment_crud,
)
from app.crud.cluster import get_cluster
from app.models.UserOrganizations import UserOrganization
from app.models.Deployment import Deployment
from app.models.Cluster import Cluster

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

router = APIRouter()

@router.post(
    "",
    response_model=DeploymentRead,
    status_code=status.HTTP_201_CREATED,
    name="create_deployment"
)
async def create_deployment_endpoint(
    data: DeploymentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    cluster_id = data.cluster_id
    cluster = await get_cluster(db, current_user, cluster_id)
    org_id = cluster.organization_id
    result = await db.execute(
        select(UserOrganization).where(
            and_(
                UserOrganization.user_id == current_user.id,
                UserOrganization.organization_id == org_id
            )
        )
    )
    membership = result.scalars().first()
    if not membership or membership.role not in [RoleEnum.Developer, RoleEnum.Admin]:
        raise HTTPException(status_code=403, detail="Only Developers or Admins can create deployments in this organization")
    return await create_deployment(db, current_user.id, org_id, cluster_id, data)

@router.get("", response_model=List[DeploymentRead], name="list_deployments")
async def list_deployments_endpoint(
    cluster_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    cluster = await get_cluster(db, current_user, cluster_id)
    org_id = cluster.organization_id
    return await list_deployments(db, current_user.id, org_id, cluster_id)

@router.get("/{deployment_id}", response_model=DeploymentRead, name="get_deployment")
async def get_deployment_endpoint(
    deployment_id: int = Path(..., description="Deployment ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    return await get_deployment_crud(db, current_user.id, deployment_id)

@router.post(
    "/{deployment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="delete_deployment"
)
async def delete_deployment_endpoint(
    request_body: DeploymentDeleteRequest,
    deployment_id: int = Path(..., description="Deployment ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(auth),
):
    cluster_id = request_body.cluster_id

    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    dep = result.scalars().first()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if dep.cluster_id != cluster_id:
        raise HTTPException(status_code=400, detail="Deployment does not belong to the specified cluster")

    result = await db.execute(
        select(Cluster).where(Cluster.id == cluster_id)
    )
    cluster = result.scalars().first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Associated cluster not found")

    org_id = cluster.organization_id

    result = await db.execute(
        select(UserOrganization).where(
            and_(
                UserOrganization.user_id == current_user.id,
                UserOrganization.organization_id == org_id
            )
        )
    )
    membership = result.scalars().first()

    if not (membership and membership.role in [RoleEnum.Developer, RoleEnum.Admin]) and dep.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this deployment")

    await delete_deployment_crud(db, deployment_id)
