from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.org import OrganizationCreate, JoinOrgRequest ,OrganizationRead
from app.core.database import AsyncSessionLocal
from app.crud import org as crud_org
from app.core.jwt import auth
from app.schemas.user import User

router = APIRouter()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/create", response_model=OrganizationRead)
async def create_organization(
    org_in: OrganizationCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(auth)
):
    return await crud_org.create_organization(db, org_in.name, current_user)

@router.post("/join")
async def join_organization(request: JoinOrgRequest, db: AsyncSession = Depends(get_async_db), current_user=Depends(auth)):
    return await crud_org.join_organization(db, current_user.id, request.invite_code)
