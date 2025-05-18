from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Organization import Organization
from app.models.UserOrganizations import UserOrganization
from app.models.Role import RoleEnum
from sqlalchemy import or_, and_
import secrets
from sqlalchemy.future import select
from fastapi import HTTPException

async def create_organization(db: AsyncSession, name: str, current_user):
    result = await db.execute(select(Organization).where(Organization.name == name))
    existing_org = result.scalars().first()
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization with this name already exists.")
    org = Organization(
        name=name,
        admin_invite_code=secrets.token_urlsafe(8),
        developer_invite_code=secrets.token_urlsafe(8),
        viewer_invite_code=secrets.token_urlsafe(8)
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    membership = UserOrganization(user_id=current_user.id, organization_id=org.id, role=RoleEnum.Admin)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return org

async def join_organization(db: AsyncSession, user_id: int, invite_code: str):
    result = await db.execute(
        select(Organization).where(
            or_(
                Organization.admin_invite_code == invite_code,
                Organization.developer_invite_code == invite_code,
                Organization.viewer_invite_code == invite_code,
            )
        )
    )
    org = result.scalars().first()
    if not org:
        raise HTTPException(status_code=400, detail="Invalid invite code.")

    if invite_code == org.admin_invite_code:
        role = RoleEnum.Admin
    elif invite_code == org.developer_invite_code:
        role = RoleEnum.Developer
    elif invite_code == org.viewer_invite_code:
        role = RoleEnum.Viewer
    else:
        raise HTTPException(status_code=400, detail="Invalid invite code.")

    exists = await db.execute(
        select(UserOrganization).where(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org.id
        )
    )
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="User already a member of this organization.")

    membership = UserOrganization(user_id=user_id, organization_id=org.id, role=role)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership

async def get_organization_by_name(db: AsyncSession, name: str):
    result = await db.execute(select(Organization).where(Organization.name == name))
    return result.scalars().first()

async def get_user_org_membership(db: AsyncSession, user_id: int, org_id: int):
    result = await db.execute(
        select(UserOrganization).where(
            and_(
                UserOrganization.user_id == user_id,
                UserOrganization.organization_id == org_id
            )
        )
    )
    return result.scalars().first()

async def get_all_organizations(db: AsyncSession):
    result = await db.execute(select(Organization))
    return result.scalars().all()

async def get_user_organizations(db: AsyncSession, user_id: int):
    result = await db.execute(select(UserOrganization).where(UserOrganization.user_id == user_id))
    memberships = result.scalars().all()
    org_ids = [m.organization_id for m in memberships]
    if not org_ids:
        return []
    result = await db.execute(select(Organization).where(Organization.id.in_(org_ids)))
    return result.scalars().all()
