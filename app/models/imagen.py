from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    public_id = Column(String)
    titulo = Column(String, nullable=True)
    descripcion = Column(String, nullable=True)
    alt = Column(String, nullable=True)
    auto_id = Column(Integer, ForeignKey("autos.id"))
    auto = relationship("Auto", back_populates="imagenes")
