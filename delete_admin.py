import sys
import os
sys.path.append(os.path.abspath('.'))

from app.database import SessionLocal
from app.models.admin import Admin

db = SessionLocal()
admin = db.query(Admin).filter(Admin.email == 'juan@sysne.ar').first()
if admin:
    db.delete(admin)
    db.commit()
    print("Admin eliminado")
else:
    print("Admin no encontrado")