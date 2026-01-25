# Concesionario Backend

API REST para el sistema de concesionario de autos.

## Tecnologías
- FastAPI
- PostgreSQL
- SQLAlchemy
- Cloudinary (para imágenes)

## Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar servidor
python run_server.py
```

## Despliegue en Railway

1. Conectar repositorio a Railway
2. Configurar variables de entorno en Railway:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALGORITHM`
   - `CLOUDINARY_URL`

## Endpoints

- `GET /` - Health check
- `POST /auth/login` - Login de admin
- `GET /marcas/` - Lista de marcas
- `GET /autos/` - Lista de autos
- `POST /autos/` - Crear auto
- `PUT /autos/{id}` - Actualizar auto
- `DELETE /autos/{id}` - Eliminar auto
- `GET /imagenes/auto/{auto_id}` - Imágenes de un auto
- `POST /imagenes/` - Subir imagen

## Documentación API

Accede a `/docs` para ver la documentación interactiva de FastAPI.