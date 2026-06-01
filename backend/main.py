import os
import re
from typing import Optional
from datetime import timedelta
from urllib.parse import quote

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, CORSMiddleware
from pydantic import BaseModel, field_validator

# Cargar variables de entorno de forma segura
load_dotenv()

# Inicializar FastAPI
app = FastAPI(title="ArchivaCloud Backend", version="1.0.0")

# ============================================================================
# MIDDLEWARE CORS (SEC-02) - Restrictivo al origen local del frontend
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIGURACIÓN DE AWS BOTO3 - Región us-west-2 con firma V4
# ============================================================================
s3_client = boto3.client(
    "s3",
    region_name="us-west-2",
    config=Config(signature_version="s3v4")
)

BUCKET_NAME = "archivacloud-p11"
PRESIGNED_URL_EXPIRATION = 3600  # 1 hora en segundos

# ============================================================================
# MODELOS PYDANTIC CON VALIDACIÓN (SEC-03)
# ============================================================================
class PresignedUrlRequest(BaseModel):
    """Modelo para solicitar una Presigned URL"""
    fileName: str
    fileType: str

    @field_validator("fileType")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Valida que la extensión sea .mp4 o .mov"""
        allowed_extensions = [".mp4", ".mov"]
        file_extension = f".{v.lower()}" if not v.startswith(".") else v.lower()
        
        if file_extension not in allowed_extensions:
            raise ValueError(
                f"Tipo de archivo no permitido. Solo se aceptan: {', '.join(allowed_extensions)}"
            )
        return v


class PresignedUrlResponse(BaseModel):
    """Modelo de respuesta con Presigned URL"""
    presignedUrl: str
    key: str
    publicUrl: str


class FileItem(BaseModel):
    """Modelo para representar un archivo en el listado"""
    name: str
    key: str
    size_bytes: int
    last_modified: str
    etag: str
    isDuplicate: bool


class FileListResponse(BaseModel):
    """Modelo de respuesta para listar archivos"""
    files: list[FileItem]
    total_count: int


class DeleteFileResponse(BaseModel):
    """Modelo de respuesta para eliminación de archivo"""
    success: bool
    message: str
    deleted_key: str


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre del archivo para evitar caracteres peligrosos.
    Mantiene solo caracteres alfanuméricos, guiones, guiones bajos y puntos.
    """
    # Remover caracteres peligrosos
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Limitar la longitud
    max_length = 255
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext
    
    return sanitized


def generate_presigned_url(
    object_key: str,
    expiration: int = PRESIGNED_URL_EXPIRATION
) -> tuple[str, str]:
    """
    Genera una Presigned URL para subir un objeto a S3.
    
    Args:
        object_key: Clave del objeto en S3
        expiration: Tiempo de expiración en segundos
    
    Returns:
        Tupla con (presigned_url, public_url)
    """
    try:
        # Generar Presigned URL para PUT
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expiration,
        )
        
        # Construir URL pública (sin parámetros de firma)
        public_url = f"https://{BUCKET_NAME}.s3.us-west-2.amazonaws.com/{quote(object_key)}"
        
        return presigned_url, public_url
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error al generar URL firmada. Por favor, intente más tarde."
        )


# ============================================================================
# ENDPOINTS
# ============================================================================
@app.get("/healthz")
async def health_check():
    """
    Endpoint de salud para verificar que el servicio está operativo.
    """
    return {"status": "healthy"}


@app.post("/api/upload/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(request: PresignedUrlRequest):
    """
    Endpoint para obtener una Presigned URL de S3 para subir archivos.
    
    Args:
        request: Objeto con fileName y fileType
    
    Returns:
        PresignedUrlResponse con presignedUrl, key y publicUrl
    
    Raises:
        HTTPException: Si la validación falla o hay error con AWS
    """
    try:
        # Sanitizar el nombre del archivo
        sanitized_name = sanitize_filename(request.fileName)
        
        if not sanitized_name:
            raise HTTPException(
                status_code=400,
                detail="Nombre de archivo inválido después de sanitización."
            )
        
        # Construir la clave del objeto con prefijo 'uploads/'
        object_key = f"uploads/{sanitized_name}"
        
        # Generar la Presigned URL
        presigned_url, public_url = generate_presigned_url(object_key)
        
        return PresignedUrlResponse(
            presignedUrl=presigned_url,
            key=object_key,
            publicUrl=public_url
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # (SEC-07) No exponer trazas de código sensibles
        raise HTTPException(
            status_code=500,
            detail="Error al procesar la solicitud. Por favor, intente más tarde."
        )


@app.get("/api/files", response_model=FileListResponse)
async def list_files():
    """
    Endpoint para listar todos los archivos en el prefijo 'uploads/' del bucket S3 (CU-02).
    Detecta y marca duplicados por nombre o ETag (Contenido Feature Extra).
    
    Returns:
        FileListResponse con lista de archivos (nombre, key, tamaño, fecha, isDuplicate)
    
    Raises:
        HTTPException: Si hay error al acceder a S3
    """
    try:
        files_raw = []
        
        # Listar todos los objetos con prefijo 'uploads/'
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix="uploads/")
        
        for page in pages:
            if "Contents" not in page:
                continue
            
            for obj in page["Contents"]:
                # Obtener nombre del archivo (sin el prefijo)
                key = obj["Key"]
                file_name = key.replace("uploads/", "", 1)
                
                # Formatear fecha de modificación
                last_modified = obj["LastModified"].isoformat()
                
                # Obtener ETag (hash MD5 del contenido)
                etag = obj.get("ETag", "").strip('"')
                
                files_raw.append({
                    "name": file_name,
                    "key": key,
                    "size_bytes": obj["Size"],
                    "last_modified": last_modified,
                    "etag": etag
                })
        
        # ====================================================================
        # DETECCIÓN DE DUPLICADOS (Feature Extra)
        # ====================================================================
        # 1. Contar ocurrencias de cada nombre
        name_count = {}
        etag_count = {}
        
        for file in files_raw:
            name = file["name"]
            etag = file["etag"]
            name_count[name] = name_count.get(name, 0) + 1
            etag_count[etag] = etag_count.get(etag, 0) + 1
        
        # 2. Marcar como duplicado si nombre o etag aparecen más de una vez
        files = []
        for file in files_raw:
            is_duplicate = (
                name_count.get(file["name"], 0) > 1 or 
                etag_count.get(file["etag"], 0) > 1
            )
            
            files.append(
                FileItem(
                    name=file["name"],
                    key=file["key"],
                    size_bytes=file["size_bytes"],
                    last_modified=file["last_modified"],
                    etag=file["etag"],
                    isDuplicate=is_duplicate
                )
            )
        
        return FileListResponse(
            files=files,
            total_count=len(files)
        )
    
    except Exception as e:
        # (SEC-07) No exponer trazas de código sensibles
        raise HTTPException(
            status_code=500,
            detail="Error al listar archivos. Por favor, intente más tarde."
        )


@app.delete("/api/files/{key:path}", response_model=DeleteFileResponse)
async def delete_file(key: str):
    """
    Endpoint para eliminar un archivo del bucket S3 (CU-04).
    
    Args:
        key: La clave completa del archivo en S3 (incluyendo prefijo)
    
    Returns:
        DeleteFileResponse con confirmación de eliminación
    
    Raises:
        HTTPException: Si hay error al acceder a S3 o si el archivo no existe
    """
    try:
        # Validar que la clave contiene el prefijo 'uploads/' para evitar eliminar archivos no autorizados
        if not key.startswith("uploads/"):
            raise HTTPException(
                status_code=403,
                detail="No autorizado para eliminar archivos fuera del prefijo 'uploads/'."
            )
        
        # Verificar que el archivo existe antes de eliminarlo
        try:
            s3_client.head_object(Bucket=BUCKET_NAME, Key=key)
        except s3_client.exceptions.NoSuchKey:
            raise HTTPException(
                status_code=404,
                detail="El archivo especificado no existe."
            )
        
        # Eliminar el objeto
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        
        return DeleteFileResponse(
            success=True,
            message="Archivo eliminado exitosamente.",
            deleted_key=key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # (SEC-07) No exponer trazas de código sensibles
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el archivo. Por favor, intente más tarde."
        )


# ============================================================================
# EVENTO DE INICIO (OPCIONAL)
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """
    Evento ejecutado al iniciar la aplicación.
    Verifica la conexión con AWS S3.
    """
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except Exception as e:
        print(f"Advertencia: No se pudo verificar acceso al bucket S3: {BUCKET_NAME}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
