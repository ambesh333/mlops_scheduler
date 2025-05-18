from pydantic import BaseModel

class OrganizationCreate(BaseModel):
    name: str

class OrganizationRead(BaseModel):
    id: int
    name: str
    admin_invite_code: str
    developer_invite_code: str
    viewer_invite_code: str

    class Config:
        orm_mode = True

class JoinOrgRequest(BaseModel):
    invite_code: str
