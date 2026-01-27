import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

def configure_cloudinary():
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if not cloudinary_url:
        raise ValueError("CLOUDINARY_URL no configurada en .env")
    cloudinary.config(cloudinary_url=cloudinary_url)

def upload_image_to_cloudinary(file, folder="autos", titulo=None, descripcion=None, alt=None):
    """
    Sube una imagen a Cloudinary y retorna la url y public_id.
    """
    configure_cloudinary()
    options = {"folder": folder}
    context_parts = []
    if titulo:
        context_parts.append(f"titulo={titulo}")
    if descripcion:
        context_parts.append(f"descripcion={descripcion}")
    if alt:
        context_parts.append(f"alt={alt}")
    if context_parts:
        options["context"] = "|".join(context_parts)
    try:
        result = cloudinary.uploader.upload(file, **options)
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        raise ValueError(f"Error al subir imagen: {str(e)}")

def delete_image_from_cloudinary(public_id):
    """
    Elimina una imagen de Cloudinary por public_id.
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result
    except Exception as e:
        raise ValueError(f"Error al eliminar imagen: {str(e)}")