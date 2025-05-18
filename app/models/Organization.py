from sqlalchemy import Column, Integer, String
from .base import Base
from sqlalchemy.orm import relationship

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    admin_invite_code = Column(String, unique=True, nullable=False)
    developer_invite_code = Column(String, unique=True, nullable=False)
    viewer_invite_code = Column(String, unique=True, nullable=False)

    members = relationship("UserOrganization", back_populates="organization")
    clusters = relationship("Cluster", back_populates="organization", cascade="all, delete-orphan")