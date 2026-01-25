import sys
import os
sys.path.append(os.path.abspath('.'))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE admins ADD COLUMN nombre_completo VARCHAR;'))
    conn.commit()
    print("Columna agregada")