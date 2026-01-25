from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Estado(Base):
    __tablename__ = "estados"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    autos = relationship("Auto", back_populates="estado")
