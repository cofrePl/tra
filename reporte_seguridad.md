# Reporte de Seguridad - ArchivaCloud (P-11)

## 1. Introducción

Este documento detalla la implementación de los 10 controles de seguridad exigidos (SEC-01 a SEC-10) en el proyecto ArchivaCloud de la Pareja P-11. El sistema implementa un gestor de videos con backend en FastAPI, frontend en React 18 y almacenamiento en AWS S3.

**Requisitos del proyecto:**
- **Formato permitido:** MP4 / MOV
- **Tamaño máximo:** 100 MB
- **Bucket S3:** archivacloud-p11
- **Región:** us-west-2
- **Origen autorizado:** http://localhost:5173

El diseño técnico garantiza que la protección de datos y operaciones cumple con los estándares de seguridad mínimos requeridos.

---

## 2. SEC-01: Secretos fuera del repositorio

Las credenciales de AWS no se subieron a GitHub. Se utiliza un archivo `.env` local que fue incluido en el `.gitignore` desde el primer commit.

**Implementación técnica:**
- El backend carga variables de entorno con `python-dotenv` y `os.environ`
- Se provee un archivo de ejemplo `.env.example` con las variables necesarias
- Variables esperadas:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION` (us-west-2)
  - `S3_BUCKET_NAME` (archivacloud-p11)
- Claves nunca se encuentran incrustadas en el código fuente

---

## 3. SEC-02: CORS restrictivo

Se configuró el bucket S3 para que rechace peticiones de cualquier origen excepto de nuestro frontend de desarrollo en `http://localhost:5173`.

**Implementación técnica:**
- FastAPI agrega middleware CORS con origen autorizado exclusivo
- Solo se aceptan solicitudes desde `http://localhost:5173`
- Evita que sitios no confiables consuman las APIs REST de la aplicación desde otros orígenes

---

## 4. SEC-03: Validación de entrada

El frontend y el backend validan estrictamente que los archivos subidos coincidan con la lista blanca asignada: solo se permiten extensiones `.mp4` y `.mov`.

**Implementación técnica:**
- Backend valida con Pydantic: `PresignedUrlRequest` valida `fileType` contra `.mp4` y `.mov`
- Función `sanitize_filename()` remueve caracteres no permitidos y evita nombres peligrosos
- La generación de la clave S3 concatena siempre el prefijo seguro `uploads/`
- Esta validación impide inyección de nombres de archivo malformados o tipos no autorizados

---

## 5. SEC-04: Límite de tamaño

Se implementó un bloqueo en la interfaz (React) y en el backend (FastAPI) para rechazar cualquier archivo que supere el tamaño máximo permitido de 100 MB.

**Implementación técnica:**
- El cliente React aplica validación inmediata antes de iniciar la subida
- Solo permite extensiones `.mp4` y `.mov`
- Rechaza archivos mayores a 100 MB
- Muestra mensajes de error claros si la selección no cumple con los requisitos
- Evita que archivos inválidos lleguen al backend o a S3

---

## 6. SEC-05: IAM de mínimo privilegio

Se creó una política de IAM específica para el usuario de la aplicación que solo permite las acciones `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` y `s3:ListBucket` exclusivamente sobre el bucket `archivacloud-p11-seba`, sin usar comodines (`*`) globales.

**Implementación técnica:**

Acciones permitidas:
- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `s3:ListBucket`

Recursos permitidos:
- `arn:aws:s3:::archivacloud-p11`
- `arn:aws:s3:::archivacloud-p11/uploads/*`

Esto garantiza que las credenciales usadas solo pueden gestionar objetos dentro del bucket y prefijo autorizado.

---

## 7. SEC-06: S3 cerrado al público

El bucket S3 tiene activada la configuración "Block Public Access". Nadie puede acceder a los videos mediante su URL directa; el acceso se realiza exclusivamente mediante URLs firmadas (Presigned URLs) temporales generadas por el backend.

**Implementación técnica:**
- El backend genera la URL firmada con `boto3.generate_presigned_url`
- El frontend realiza `PUT` directo al endpoint S3 usando Axios
- La URL pública se construye con `https://archivacloud-p11.s3.us-west-2.amazonaws.com/{key}`
- Este modelo evita que las credenciales de AWS se expongan al cliente
- Asegura que el tráfico de subida se realice sobre TLS

---

## 8. SEC-07: Errores sin información sensible

El backend de FastAPI utiliza `HTTPException` para devolver mensajes genéricos sin exponer el *stack trace* interno ni la estructura del código en caso de fallos.

**Implementación técnica:**
- Todos los endpoints envuelven la lógica crítica en bloques `try/except`
- Errores de AWS devuelven `HTTP 500` con mensajes genéricos (ej: "El archivo no existe")
- No se exponen trazas de stack o detalles internos al cliente
- Errores de validación controlados retornan códigos HTTP apropiados (400, 403, 404)
- Protege contra la divulgación de información sensible en producción

---

## 9. SEC-08: Encriptación en reposo

El bucket de Amazon S3 almacena todos los videos encriptados por defecto utilizando el cifrado del lado del servidor gestionado por Amazon (SSE-S3).

**Implementación técnica:**
- Cifrado automático en el servidor S3
- Cumplimiento de requisitos de almacenamiento seguro
- Datos protegidos en reposo sin acción manual requerida

---

## 10. SEC-09: Escaneo de dependencias

Se ejecutó `pip-audit` en el backend, mitigando las alertas mediante la actualización de `pip`. En el frontend se ejecutó `npm audit`, justificando la no corrección forzada de dependencias *Moderate* en Vite para no comprometer la estabilidad del sistema con *breaking changes*.

**Implementación técnica:**
- Backend: `pip-audit` y análisis de paquetes en `requirements.txt`
- Frontend: `npm audit` y revisión de dependencias en `package.json`
- Los resultados se mantienen documentados en archivos de auditoría
- Archivos de reporte: `SECURITY_REPORT_BACKEND.txt/json` y `SECURITY_REPORT_FRONTEND.txt/json`

---

## 11. SEC-10: TLS de extremo a extremo

Toda la comunicación entre el backend y Amazon S3 se realiza bajo el protocolo seguro HTTPS, garantizando la encriptación de los datos en tránsito.

**Implementación técnica:**
- Todas las conexiones a S3 utilizan HTTPS
- Protección de datos durante la transmisión
- Evita interceptación de datos en tránsito

---

## 12. Conclusión

El proyecto ArchivaCloud de la Pareja P-11 implementa de manera integral los 10 controles de seguridad obligatorios. El diseño técnico asegura que:

- Los archivos subidos cumplen las restricciones de formato y tamaño (MP4/MOV, 100 MB máximo)
- Las credenciales están protegidas y nunca se exponen en el repositorio
- El acceso a S3 está limitado mediante URLs presignadas y políticas IAM restrictivas
- La comunicación es segura de extremo a extremo (HTTPS/TLS)
- Los errores no revelan información sensible
- Las dependencias están auditadas regularmente

Tanto el backend como el frontend operan sobre el bucket `archivacloud-p11` en la región `us-west-2` con controles de origen restrictivos y validación exhaustiva en múltiples capas.
