import sys
import os
sys.path.append(os.path.abspath('.'))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("DELETE FROM admins WHERE email = 'juan@sysne.ar'"))
    conn.commit()
    print("Admin eliminado")