from pydantic import BaseModel

class ImagenBase(BaseModel):
    url: str
    public_id: str
    titulo: str | None = None
    descripcion: str | None = None
    alt: str | None = None
    auto_id: int

class ImagenCreate(ImagenBase):
    pass

class ImagenOut(ImagenBase):
    id: int
    class Config:
        from_attributes = True
