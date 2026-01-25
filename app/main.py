
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
    auth
)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/")
def root():
    return {"message": "API Concesionario funcionando"}
