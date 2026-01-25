from pydantic import BaseModel

class ImagenBase(BaseModel):
    url: str
    public_id: str
    auto_id: int

class ImagenCreate(ImagenBase):
    pass

class ImagenOut(ImagenBase):
    id: int
    class Config:
        from_attributes = True
