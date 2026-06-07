# ArchivaCloud - Pareja P-11

## Nombre del Producto

**ArchivaCloud**

Aplicación web para gestión segura de videos que permite subir, listar, descargar y eliminar archivos almacenados en AWS S3.

## Integrantes

- Pareja P-11
- Integrante 1: [sebastian cofre]
- Integrante 2: [lucas espinoza]

## Fila de Parámetros del Anexo B

- Formato permitido: **MP4 / MOV**
- Tamaño máximo: **100 MB**
- Bucket S3: **archivacloud-p11**
- Región AWS: **us-west-2**
- Prefijo seguro: **uploads/**
- Origen frontend permitido: **http://localhost:5173**

## Variables de Entorno Necesarias

El backend requiere las siguientes variables de entorno para funcionar correctamente:

```env
Access Key: 
Secret Key: 
Session Token:
AWS_REGION=us-east-1
```

Recomendación: copiar `backend/.env.example` a `backend/.env` y no incluir el archivo `.env` en el control de versiones.

Para ver el prompt exacto y la guía paso a paso de AWS Academy, consulta `docs/aws-s3-p11-setup.md`.

## Política IAM Mínima en Formato JSON

La política IAM mínima para el proyecto concede solo los permisos necesarios para la lectura, escritura y eliminación en el prefijo `uploads/` del bucket `archivacloud-p11`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::archivacloud-p11"
      ]
    },
    {
      "Sid": "ObjectAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::archivacloud-p11/uploads/*"
      ]
    }
  ]
}
```

## Configuración CORS del Bucket en JSON

El bucket `archivacloud-p11-seba` debe configurar CORS para permitir únicamente los orígenes locales del frontend y los métodos usados por la aplicación:

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:5173",
      "http://127.0.0.1:5173"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "POST",
      "DELETE"
    ],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": [],
    "MaxAgeSeconds": 3000
  }
]
```

## Instrucciones para Ejecutar el Backend (FastAPI)

1. Abrir terminal en la carpeta `backend`.
2. Crear y activar el entorno virtual:

```bash
cd backend
python -m venv .
.\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear el archivo de configuración:

```bash
copy .env.example .env
```

5. Ejecutar la API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. Verificar el backend en:

- `http://localhost:8000`
- Documentación Swagger: `http://localhost:8000/docs`

## Instrucciones para Ejecutar el Frontend (React + Vite)

1. Abrir terminal en la carpeta `frontend`.
2. Instalar dependencias:

```bash
cd frontend
npm install
```

3. Iniciar el servidor de desarrollo:

```bash
npm run dev
```

4. Abrir la aplicación en:

- `http://localhost:5173`

## Marcadores para Documentación Visual

- Diagrama manuscrito: `docs/arquitectura.jpg`
- Screencast: [Insertar enlace al screencast aquí]

## Estructura del Repositorio

```text
tra/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── SECURITY_REPORT_BACKEND.json
│   └── SECURITY_REPORT_BACKEND.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── docs/
│   └── arquitectura.jpg
├── SEC-09_AUDIT_REPORT.md
├── SEC-09_SECURITY_AUDIT_GUIDE.md
├── DETECCION_DUPLICADOS.md
├── reporte_seguridad.md
└── README.md
```

