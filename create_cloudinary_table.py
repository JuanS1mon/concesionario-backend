#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models.configuracion_cloudinary import ConfiguracionCloudinary

def create_tables():
    # Crear la tabla de configuración de Cloudinary
    ConfiguracionCloudinary.__table__.create(bind=engine, checkfirst=True)
    print("Tabla configuracion_cloudinary creada exitosamente")

if __name__ == "__main__":
    create_tables()