from pydantic import BaseModel
from typing import Optional

class ImagenBase(BaseModel):
    url: str
    public_id: Optional[str] = None
    auto_id: int

class ImagenCreate(ImagenBase):
    pass

class ImagenOut(ImagenBase):
    id: int
    class Config:
        from_attributes = True
