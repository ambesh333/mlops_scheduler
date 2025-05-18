from sqlalchemy import Column, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.Role import RoleEnum
from .base import Base


class UserOrganization(Base):
    __tablename__ = "user_organization"
    __table_args__ = (UniqueConstraint('user_id', 'organization_id', name='uix_user_org'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="members")