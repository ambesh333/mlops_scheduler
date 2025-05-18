# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.models.base import Base  
# Import all models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.Cluster import Cluster
from app.models.Deployment import Deployment
from app.models.Organization import Organization
from app.models.UserOrganizations import UserOrganization


engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
