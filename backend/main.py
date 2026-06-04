import os
import re
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from starlette.middleware.cors import CORSMiddleware

load_dotenv()

AWS_REGION = "us-west-2"
BUCKET_NAME = "archivacloud-p11"
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
)


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


@app.get("/healthz")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/upload/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(request: PresignedUrlRequest):
    sanitized_name = sanitize_filename(request.fileName)
    if not sanitized_name:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    object_key = f"{UPLOAD_PREFIX}{sanitized_name}"
    presigned_url, public_url = generate_presigned_url(object_key)

    return PresignedUrlResponse(
        presignedUrl=presigned_url,
        key=object_key,
        publicUrl=public_url,
    )


@app.get("/api/files", response_model=list[FileItem])
async def list_files():
    raw_files = []
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=UPLOAD_PREFIX)

    for page in pages:
        if "Contents" not in page:
            continue
        for obj in page["Contents"]:
            key = obj["Key"]
            if key == UPLOAD_PREFIX:
                continue
            file_name = key.replace(UPLOAD_PREFIX, "", 1)
            raw_files.append(
                {
                    "name": file_name,
                    "key": key,
                    "size": obj["Size"],
                    "lastModified": obj["LastModified"].isoformat(),
                    "etag": obj.get("ETag", "").strip('"'),
                }
            )

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
            (file["etag"] and etag_counts.get(file["etag"], 0) > 1)
        )
        files.append(
            FileItem(
                name=file["name"],
                key=file["key"],
                size=file["size"],
                lastModified=file["lastModified"],
                isDuplicate=is_duplicate,
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
