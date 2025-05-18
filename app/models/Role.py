import enum

class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    Developer = "Developer"
    Viewer = "Viewer"