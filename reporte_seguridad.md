# Reporte de Seguridad - ArchivaCloud (P-11)

## 1. Introducción

Este documento detalla cómo implementamos los 10 controles de seguridad exigidos (SEC-01 a SEC-10) en ArchivaCloud, nuestro gestor de videos. El sistema está construido con FastAPI en el backend, React 18 en el frontend, y AWS S3 para almacenar los videos.

**Lo que necesitábamos cumplir:**
- **Formato permitido:** MP4 / MOV
- **Tamaño máximo:** 100 MB
- **Bucket S3:** archivacloud-p11
- **Región:** us-west-2
- **Origen autorizado:** http://localhost:5173

A continuación te mostramos cómo aseguramos cada aspecto del sistema.

---

## 2. SEC-01: Secretos fuera del repositorio

Nunca subimos nuestras credenciales de AWS a GitHub. Desde el primer commit, usamos un archivo `.env` local que está en el `.gitignore`. Si alguien accede al repositorio, no encuentra nada sensible.

**Cómo lo hicimos:**
- El backend carga todo desde variables de entorno usando `python-dotenv`
- Proporcionamos un `.env.example` para que otros sepan qué variables necesitan
- Variables principales:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION` (us-west-2)
  - `S3_BUCKET_NAME` (archivacloud-p11)
- Las claves nunca están hardcodeadas en el código

---

## 3. SEC-02: CORS restrictivo

No queremos que cualquier sitio web en internet pueda llamar a nuestras APIs. Solo permitimos requests desde nuestro frontend en `http://localhost:5173`.

**Cómo lo hicimos:**
- FastAPI tiene un middleware CORS que solo acepta ese origen
- Si alguien intenta desde otro sitio, la petición se bloquea automáticamente
- Esto evita ataques desde páginas maliciosas

---

## 4. SEC-03: Validación de entrada

Nos aseguramos de que solo se suban videos en los formatos que queremos (MP4 y MOV). Tanto el frontend como el backend lo verifican, así no colapsa nada raro.

**Cómo lo hicimos:**
- El backend valida con Pydantic que el tipo de archivo sea `.mp4` o `.mov`
- Limpiamos los nombres de archivo para quitar caracteres peligrosos
- Siempre generamos las claves S3 con el prefijo `uploads/` para mantener todo organizado
- Si alguien intenta subir algo raro, lo bloqueamos antes de que llegue a S3

---

## 5. SEC-04: Límite de tamaño

No queremos que suban archivos gigantes. El límite es 100 MB, y lo verificamos en dos lugares: el navegador y el servidor.

**Cómo lo hicimos:**
- React valida el tamaño antes de permitir la subida
- Si pasas un archivo muy grande, te muestra un mensaje de error enseguida
- El backend también verifica, por si acaso
- Esto evita desperdiciar ancho de banda y almacenamiento

---

## 6. SEC-05: IAM de mínimo privilegio

Nuestra aplicación solo tiene permisos para hacer lo que necesita en AWS. No le dimos acceso a todo, solo a subir, descargar y eliminar videos en nuestro bucket.

**Qué permisos tiene:**
- Subir archivos (`s3:PutObject`)
- Descargar archivos (`s3:GetObject`)
- Eliminar archivos (`s3:DeleteObject`)
- Listar lo que hay en el bucket (`s3:ListBucket`)

**Dónde pueden hacerlo:**
- Solo en `archivacloud-p11`
- Solo en la carpeta `uploads/`

Si alguien roba las credenciales, no pueden hacer mucho más de lo que la app necesita.

---

## 7. SEC-06: S3 cerrado al público

Nadie puede acceder a los videos si no tiene un enlace especial. El bucket está bloqueado al público, así que no puedes meterte a una URL cualquiera y descargar videos.

**Cómo lo hicimos:**
- El backend genera URLs firmadas temporales (tipo "código de acceso")
- Cuando subes o descargas, usas esa URL temporal, no tus credenciales de AWS
- Los videos en S3 están encriptados
- Todo viaja por HTTPS, así que nadie puede interceptar en el camino

---

## 8. SEC-07: Errores sin información sensible

Cuando algo falla, no le decimos al usuario detalles técnicos que podrían ayudar a un atacante. Solo mensajes simples.

**Cómo lo hicimos:**
- Si hay un error, el usuario ve algo como "El archivo no existe" o "No tienes permiso"
- Nunca mostramos el código interno ni dónde explotó la aplicación
- Los mensajes de error son genéricos pero útiles para quien usa la app
- Esto evita que alguien descubra cómo funciona internamente

---

## 9. SEC-08: Encriptación en reposo

Los videos se guardan encriptados en S3. Aunque alguien acceda a los servidores de Amazon, no puede ver el contenido sin la clave.

**Cómo lo hicimos:**
- S3 encripta todo automáticamente
- Amazon maneja las claves de encriptación
- No hay que hacer nada extra, funciona por defecto

---

## 10. SEC-09: Escaneo de dependencias

Todas nuestras librerías las revisamos para asegurarnos de que no tengan agujeros de seguridad conocidos.

**Cómo lo hicimos:**
- En el backend: `pip-audit` revisa los paquetes Python
- En el frontend: `npm audit` revisa los paquetes Node
- Actualizamos lo que podemos sin romper cosas
- Los resultados están documentados en `SECURITY_REPORT_BACKEND.txt/json` y `SECURITY_REPORT_FRONTEND.txt/json`

---

## 11. SEC-10: TLS de extremo a extremo

Toda la comunicación que hacemos con S3 va encriptada. Nadie puede interceptar los videos en el camino.

**Cómo lo hicimos:**
- Siempre usamos HTTPS
- Los datos van encriptados de un lado a otro
- Así aunque alguien esté escuchando en la red, no ve nada útil

---

## 12. Conclusión

ArchivaCloud está construido con seguridad desde el principio. Hemos implementado todas las 10 defensas obligatorias:

- **Validación:** Solo aceptamos MP4 y MOV, máximo 100 MB
- **Secretos seguros:** Las credenciales nunca ven la luz
- **Acceso restringido:** Solo nuestra app puede usar las APIs
- **Permisos mínimos:** AWS solo nos deja hacer lo necesario
- **Almacenamiento seguro:** Los videos están encriptados en S3
- **Comunicación encriptada:** Todo viaja por HTTPS
- **Errores amables:** Si algo falla, no revelamos detalles peligrosos
- **Dependencias limpias:** Auditamos todo regularmente

Basicamente, hicimos que sea difícil atacar la app sin que sea incómodo de usar.
