from pydantic import BaseModel
from typing import Optional

class AdminBase(BaseModel):
    email: str
    nombre_completo: Optional[str] = None

class AdminCreate(AdminBase):
    contrasena: str

class AdminUpdate(BaseModel):
    email: Optional[str] = None
    nombre_completo: Optional[str] = None
    contrasena: Optional[str] = None

class Admin(AdminBase):
    id: int
    class Config:
        from_attributes = True
