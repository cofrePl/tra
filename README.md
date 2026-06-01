# ArchivaCloud - Portal P-11

Proyecto del repositorio ArchivaCloud para la Pareja P-11.

## 🚀 Parámetros Únicos Asignados
- Tipos de archivo permitidos: **MP4 / MOV**
- Tamaño máximo: **100 MB**
- Bucket de S3: **archivacloud-p11**
- Región de AWS: **us-west-2**
- Feature extra: **Detección de archivos duplicados**

---

## 🧠 Arquitectura

El sistema está dividido en dos capas principales:
- **Backend:** FastAPI que provee API REST y genera URLs presignadas de S3.
- **Frontend:** React 18 con Vite que consume las APIs y presenta un panel interactivo.

La foto del diagrama manuscrito se colocará en:

`docs/arquitectura.jpg`

---

## 🛠 Stack Tecnológico

### Backend
- Python 3.10+
- FastAPI
- Boto3
- Pydantic
- python-dotenv
- Uvicorn

### Frontend
- React 18
- Vite
- Axios
- CSS moderno

### AWS y Seguridad
- AWS S3 Bucket `archivacloud-p11`
- Región `us-west-2`
- CORS restringido a `http://localhost:5173`
- Auditorías SEC-09 con `pip-audit` y `npm audit`

---

## 🔧 Variables de Entorno

El backend usa un archivo `.env` local; el ejemplo está en `.env.example`.

### `.env.example`
```env
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-west-2
S3_BUCKET_NAME=archivacloud-p11
```

No subas el archivo `.env` al repositorio. Está protegido por `.gitignore`.

---

## 🔐 Política IAM de Mínimo Privilegio (SEC-05)

Ejemplo de política IAM que permite solo las acciones necesarias en el bucket `archivacloud-p11`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::archivacloud-p11",
        "arn:aws:s3:::archivacloud-p11/uploads/*"
      ]
    }
  ]
}
```

---

## 🌐 Configuración CORS del Bucket (SEC-02)

Ejemplo de configuración CORS para el bucket:

```json
[
  {
    "AllowedOrigins": ["http://localhost:5173"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

---

## 📁 Estructura del Proyecto

```
tra/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
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
│   ├── index.html
│   ├── SECURITY_REPORT_FRONTEND.json
│   └── SECURITY_REPORT_FRONTEND.txt
├── docs/
│   └── arquitectura.jpg
├── SEC-09_AUDIT_REPORT.md
├── SEC-09_SECURITY_AUDIT_GUIDE.md
├── DETECCION_DUPLICADOS.md
└── README.md
```

---

## 🧰 Instalación y Despliegue

### 1. Clonar el repositorio

```bash
cd c:\Users\THN_LAB\Desktop
git clone <URL_DEL_REPOSITORIO>
cd tra
```

### 2. Backend

```bash
cd backend
python -m venv .
.\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Levantar Backend

```bash
cd backend
.\Scripts\activate
uvicorn main:app --reload
```

- Backend en: **http://localhost:8000**
- Swagger: **http://localhost:8000/docs**

### 5. Levantar Frontend

```bash
cd frontend
npm run dev
```

- Frontend en: **http://localhost:5173**

---

## 📌 Parámetros del Proyecto

- **Tipos admitidos:** MP4, MOV
- **Máximo permitido:** 100 MB
- **Bucket S3:** archivacloud-p11
- **Región AWS:** us-west-2
- **Feature extra:** Detección de archivos duplicados

---

## 📚 Documentación Adicional

- [Guía SEC-09 Completa](SEC-09_SECURITY_AUDIT_GUIDE.md)
- [Reporte SEC-09 Consolidado](SEC-09_AUDIT_REPORT.md)
- [Detección de Duplicados](DETECCION_DUPLICADOS.md)

---

## 📝 Notas Finales

Este README sigue la plantilla del Anexo D para la Pareja P-11. Incluye los parámetros únicos, el stack tecnológico, la política IAM mínima y la configuración CORS requerida. Mantén actualizado el diagrama en `docs/arquitectura.jpg` y los reportes de auditoría para cumplir con SEC-09.
