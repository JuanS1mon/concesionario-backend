#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.cloudinary_service import configure_cloudinary

if __name__ == "__main__":
    try:
        configure_cloudinary()
        print("Configuración de Cloudinary exitosa.")
    except ValueError as e:
        print(f"Error: {e}")