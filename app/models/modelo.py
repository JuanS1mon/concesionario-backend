from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Modelo(Base):
    __tablename__ = "modelos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    marca_id = Column(Integer, ForeignKey("marcas.id"))
    autos = relationship("Auto", back_populates="modelo")
