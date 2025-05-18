from sqlalchemy import Column, Integer, String
from .base import Base
from sqlalchemy.orm import relationship
from app.models.Deployment import Deployment

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    organizations = relationship("UserOrganization", back_populates="user")
    clusters   = relationship("Cluster", back_populates="owner", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="owner", cascade="all, delete-orphan")
