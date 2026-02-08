
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Force redeploy

from app.api import (
    autos,
    marcas,
    modelos,
    estados,
    cotizaciones,
    configuracion_cloudinary,
    imagenes,
    auth,
    clientes,
    oportunidades,
    ventas
)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://concesionario-frontend-production.up.railway.app",
        "http://concesionario-frontend-production.up.railway.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.2:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(autos.router)
app.include_router(marcas.router)
app.include_router(modelos.router)
app.include_router(estados.router)
app.include_router(cotizaciones.router)
app.include_router(configuracion_cloudinary.router)
app.include_router(imagenes.router)
app.include_router(clientes.router)
app.include_router(oportunidades.router)
app.include_router(ventas.router)

@app.get("/")
def root():
    return {"message": "API Concesionario funcionando"}
