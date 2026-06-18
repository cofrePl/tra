import os
import re
import uuid
from datetime import datetime
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from starlette.middleware.cors import CORSMiddleware

load_dotenv()

AWS_REGION = "us-east-1"
BUCKET_NAME = "archivacloud-p11-seba"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
UPLOAD_PREFIX = "uploads/"
PRESIGNED_URL_EXPIRATION = 3600
ALLOWED_ORIGINS = ["http://localhost:5173"]
ALLOWED_EXTENSIONS = {".mp4", ".mov"}

app = FastAPI(title="ArchivaCloud Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    config=Config(signature_version="s3v4"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN")
)

table = dynamodb.Table("videos_cloud")


class PresignedUrlRequest(BaseModel):
    fileName: str
    fileType: str
    fileSize: int

    @field_validator("fileType")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        extension = f".{v.lower()}" if not v.startswith(".") else v.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("Solo se permiten archivos .mp4 y .mov.")
        return v

    @field_validator("fileSize")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        if v <= 0 or v > MAX_FILE_SIZE_BYTES:
            raise ValueError("El tamaño del archivo debe ser máximo 100 MB.")
        return v


class PresignedUrlResponse(BaseModel):
    presignedUrl: str
    key: str
    publicUrl: str


class FileItem(BaseModel):
    name: str
    key: str
    size: int
    lastModified: str
    isDuplicate: bool
    url: str


class DeleteFileResponse(BaseModel):
    success: bool
    message: str
    deleted_key: str


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255 - len(ext)] + ext
    return sanitized


def generate_presigned_url(object_key: str, expiration: int = PRESIGNED_URL_EXPIRATION) -> tuple[str, str]:
    try:
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expiration,
        )
        public_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{quote(object_key)}"
        return presigned_url, public_url
    except Exception:
        raise HTTPException(status_code=500, detail="Error al generar la URL firmada.")


def generate_get_presigned_url(object_key: str, expiration: int = PRESIGNED_URL_EXPIRATION) -> str:
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expiration,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error al generar la URL firmada de descarga.")


@app.get("/healthz")
async def health_check():
    return {"status": "healthy"}


def extract_original_filename_from_key(key: str) -> str:
    file_name = key.replace(UPLOAD_PREFIX, "", 1)
    match = re.match(r"^[0-9a-f]{32}_(.+)$", file_name)
    return match.group(1) if match else file_name


@app.post("/api/upload/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(request: PresignedUrlRequest):
    sanitized_name = sanitize_filename(request.fileName)
    if not sanitized_name:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    file_id = uuid.uuid4().hex
    object_key = f"{UPLOAD_PREFIX}{file_id}_{sanitized_name}"
    presigned_url, public_url = generate_presigned_url(object_key)

    try:
        table.put_item(
            Item={
                "file_id": file_id,
                "display_name": sanitized_name,
                "upload_date": datetime.utcnow().isoformat(),
                "s3_key": object_key,
                "size": request.fileSize,
            }
        )
    except ClientError:
        raise HTTPException(status_code=500, detail="Error al insertar el registro en DynamoDB.")

    return PresignedUrlResponse(
        presignedUrl=presigned_url,
        key=object_key,
        publicUrl=public_url,
    )


@app.get("/api/files", response_model=list[FileItem])
async def list_files():
    raw_files = []
    scan_kwargs = {}

    try:
        while True:
            response = table.scan(**scan_kwargs)
            for item in response.get("Items", []):
                key = item.get("s3_key")
                if not key:
                    continue

                file_name = item.get("display_name") or extract_original_filename_from_key(key)
                file_url = generate_get_presigned_url(key)

                raw_files.append(
                    {
                        "name": file_name,
                        "key": key,
                        "size": item.get("size", 0),
                        "lastModified": item.get("upload_date", ""),
                        "etag": "",
                        "url": file_url,
                    }
                )

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key
    except ClientError:
        raise HTTPException(status_code=500, detail="Error al leer los registros de DynamoDB.")

    name_counts = {}
    etag_counts = {}
    for file in raw_files:
        name_counts[file["name"]] = name_counts.get(file["name"], 0) + 1
        if file["etag"]:
            etag_counts[file["etag"]] = etag_counts.get(file["etag"], 0) + 1

    files = []
    for file in raw_files:
        is_duplicate = (
            name_counts.get(file["name"], 0) > 1 or
            (bool(file["etag"]) and etag_counts.get(file["etag"], 0) > 1)
        )
        files.append(
            FileItem(
                name=file["name"],
                key=file["key"],
                size=file["size"],
                lastModified=file["lastModified"],
                isDuplicate=bool(is_duplicate),
                url=file["url"],
            )
        )
    return files


@app.delete("/api/files/{key:path}", response_model=DeleteFileResponse)
async def delete_file(key: str):
    if not key.startswith(UPLOAD_PREFIX):
        raise HTTPException(status_code=403, detail="El archivo debe estar en uploads/.")

    try:
        s3_client.head_object(Bucket=BUCKET_NAME, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(status_code=404, detail="El archivo no existe.")
        raise HTTPException(status_code=500, detail="Error al verificar el objeto en S3.")

    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        return DeleteFileResponse(
            success=True,
            message="Archivo eliminado exitosamente.",
            deleted_key=key,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error al eliminar el archivo.")


@app.on_event("startup")
async def startup_event():
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except Exception:
        print(f"Advertencia: no se pudo conectar al bucket {BUCKET_NAME} en {AWS_REGION}.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/download-url")
def get_download_url(filename: str):
    try:
        # Generar una URL firmada para LEER el archivo (dura 1 hora)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME, 
                'Key': f"{UPLOAD_PREFIX}{filename}"
            },
            ExpiresIn=3600
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
