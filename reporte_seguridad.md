# Reporte de Seguridad para Pareja P-11

## 1. Introducción

Este documento describe el cumplimiento de los controles mínimos de seguridad SEC-01 a SEC-10 para el proyecto ArchivaCloud de la Pareja P-11. El sistema implementa un gestor de videos con backend en FastAPI, frontend en React 18 y almacenamiento en AWS S3. El bucket utilizado es `archivacloud-p11`, ubicado en la región `us-west-2`. Los requisitos específicos del proyecto para la pareja P-11 son:

- Formato permitido: **MP4 / MOV**
- Tamaño máximo: **100 MB**
- Bucket S3: **archivacloud-p11**
- Región: **us-west-2**

Este reporte describe las medidas técnicas adoptadas para cada control y cómo se garantiza la protección de datos y operaciones.

## 2. SEC-01: Gestión de secretos y configuración de entorno

El backend usa variables de entorno para credenciales y configuración sensible. Se provee un archivo de ejemplo `.env.example` con las variables necesarias, pero las credenciales reales no se almacenan en el repositorio.

- Variables esperadas:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION` (`us-west-2`)
  - `S3_BUCKET_NAME` (`archivacloud-p11`)

La carga de configuración se realiza con `python-dotenv` y `os.environ`, evitando claves incrustadas en el código fuente.

## 3. SEC-02: Control de origen y CORS restringido

El frontend y backend están configurados para trabajar desde dominios locales controlados. FastAPI agrega middleware CORS con origen autorizado exclusivo:

- `http://localhost:5173`

Esto evita que sitios no confiables consuman las APIs REST de la aplicación desde otros orígenes.

## 4. SEC-03: Validación y sanitización en el backend

El backend valida estrictamente los parámetros de subida usando Pydantic.

- `PresignedUrlRequest` valida `fileType` contra `.mp4` y `.mov`
- `sanitize_filename()` remueve caracteres no permitidos y evita nombres peligrosos
- La generación de la clave S3 concatena siempre el prefijo seguro `uploads/`

Esta validación impide que un actor inyecte nombres de archivo malformados o tipos no autorizados en la lógica de generación de URLs firmadas.

## 5. SEC-04: Validación en el frontend de formatos y tamaño

El cliente React aplica validación inmediata del archivo seleccionado antes de iniciar la subida.

- Solo permite extensiones `.mp4` y `.mov`
- Rechaza archivos mayores a **100 MB**
- Muestra mensajes de error claros si la selección no cumple con los requisitos

Esto cumple con el flujo SEC-04 al evitar que archivos inválidos lleguen al backend o a S3.

## 6. SEC-05: Principio de mínimo privilegio IAM

El proyecto define una política IAM mínima para permisos de S3.

Acciones permitidas:

- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `s3:ListBucket`

Recursos permitidos:

- `arn:aws:s3:::archivacloud-p11`
- `arn:aws:s3:::archivacloud-p11/uploads/*`

Esto garantiza que los credenciales usados solo pueden gestionar objetos dentro del bucket y prefijo autorizado.

## 7. SEC-06: Protección de transferencia y almacenamiento de archivos

La aplicación utiliza URLs presignadas para subir directamente a S3 sobre HTTPS.

- El backend genera la URL firmada con `boto3.generate_presigned_url`
- El frontend realiza `PUT` directo al endpoint S3 usando Axios
- La URL pública se construye con `https://archivacloud-p11.s3.us-west-2.amazonaws.com/{key}`

Este modelo evita que las credenciales de AWS se expongan al cliente y asegura que el tráfico de subida se realice sobre TLS.

## 8. SEC-07: Manejo seguro de errores y no exposición de trazas

Todos los endpoints del backend envuelven la lógica crítica en bloques `try/except`.

- Errores de AWS devuelven `HTTP 500` con mensajes genéricos
- No se exponen trazas de stack o detalles internos al cliente
- Errores de validación controlados retornan códigos HTTP apropiados (400, 403, 404)

Esto protege contra la divulgación de información sensible en producción.

## 9. SEC-08: Detección de duplicados y control de integridad

El endpoint `GET /api/files` analiza los objetos listados en S3 y marca duplicados con la propiedad booleana `isDuplicate` cuando:

- comparten el mismo nombre de archivo (`name`)
- comparten el mismo hash de contenido (`ETag`)

Esta lógica de detección asegura que la aplicación puede identificar colisiones de contenido y alertar al usuario sobre archivos repetidos.

## 10. SEC-09: Auditoría de dependencias y revisión de seguridad

La aplicación cuenta con reportes de auditoría de dependencias para backend y frontend.

- Backend: `pip-audit` y análisis de paquetes en `requirements.txt`
- Frontend: `npm audit` y revisión de dependencias en `package.json`

Los resultados se mantienen documentados en archivos de auditoría (`SECURITY_REPORT_BACKEND.*`, `SECURITY_REPORT_FRONTEND.*`).

## 11. SEC-10: Operaciones y control de eliminación

El flujo de eliminación de archivos incluye verificación y confirmación.

- El endpoint `DELETE /api/files/{key:path}` valida que la ruta comience con `uploads/`
- Se utiliza `head_object` para validar existencia
- Se elimina el objeto solo si cumple el prefijo seguro

En el frontend se agrega confirmación explícita vía `window.confirm` antes de realizar cualquier eliminación.

## 12. Conclusión

El proyecto ArchivaCloud de la Pareja P-11 implementa controles de seguridad integrales sobre la gestión de credenciales, validación de archivos, permisos mínimos de AWS, protección de errores, y detección de duplicados usando S3.

El diseño técnico asegura que los archivos subidos cumplen las restricciones de formato y tamaño (`MP4/MOV`, `100 MB`), y que tanto backend como frontend operan sobre el bucket `archivacloud-p11` en `us-west-2` con controles de origen y políticas restrictivas.
