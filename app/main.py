
# Forzar carga de .env siempre
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Force redeploy

from app.api import (
    autos,
    marcas,
    modelos,
    estados,
    cotizaciones,
    configuracion_cloudinary,
    configuracion_ai,
    imagenes,
    auth,
    clientes,
    oportunidades,
    ventas,
    pricing,
    market
)

app = FastAPI(root_path="")

# Middleware para confiar en headers del proxy (Railway)
@app.middleware("http")
async def force_https_redirects(request, call_next):
    # Si el proxy indica HTTPS, forzar el scheme
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    # En desarrollo permitir todos los orígenes para evitar bloqueos CORS.
    # Cambiar a orígenes específicos en producción.
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
app.include_router(configuracion_ai.router)
app.include_router(imagenes.router)
app.include_router(clientes.router)
app.include_router(oportunidades.router)
app.include_router(ventas.router)
app.include_router(pricing.router)
app.include_router(market.router)

@app.get("/")
def root():
    return {"message": "API Concesionario funcionando"}
