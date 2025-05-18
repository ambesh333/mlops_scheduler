# app/api/user.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate
from app.core.database import AsyncSessionLocal
from app.crud import user as crud_user
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.schemas.token import Token

router = APIRouter()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    db_user = await crud_user.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    return await crud_user.create_user(db, user.username,user.password)

@router.post("/login", response_model=Token)
async def login(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    db_user = await crud_user.get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": db_user.username, "user_id": db_user.id})
    return {"access_token": access_token, "token_type": "bearer"}
