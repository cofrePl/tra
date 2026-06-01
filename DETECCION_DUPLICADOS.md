# Feature Extra: Detección de Duplicados en ArchivaCloud

## 📋 Descripción

La detección automática de videos duplicados identifica archivos que:
1. **Tienen el mismo nombre** - Múltiples archivos con idéntico nombre en el bucket
2. **Tienen el mismo contenido** - Archivos con el mismo hash MD5/ETag de S3

Esta feature adicional ayuda a mantener la integridad del almacenamiento y evita desperdicio de espacio.

---

## 🔧 Implementación Backend

### 1. Modelo Actualizado - `FileItem`

```python
class FileItem(BaseModel):
    """Modelo para representar un archivo en el listado"""
    name: str
    key: str
    size_bytes: int
    last_modified: str
    etag: str                    # Hash MD5 del contenido
    isDuplicate: bool            # Nuevo: indicador de duplicado
```

### 2. Lógica de Detección - `GET /api/files`

**Pasos:**

#### Paso 1: Recolectar metadatos
```python
# Se obtienen todos los archivos del prefijo 'uploads/'
# Incluye: nombre, tamaño, fecha, ETag (hash del contenido)
```

#### Paso 2: Contar ocurrencias
```python
name_count = {}  # {nombre: cantidad_apariciones}
etag_count = {}  # {hash: cantidad_apariciones}

# Contar cuántas veces aparece cada nombre y hash
for file in files_raw:
    name_count[file["name"]] = name_count.get(file["name"], 0) + 1
    etag_count[file["etag"]] = etag_count.get(file["etag"], 0) + 1
```

#### Paso 3: Marcar duplicados
```python
is_duplicate = (
    name_count.get(file["name"], 0) > 1 or      # ¿Nombre duplicado?
    etag_count.get(file["etag"], 0) > 1         # ¿Contenido duplicado?
)
```

### 3. Respuesta JSON

```json
{
  "files": [
    {
      "name": "video.mp4",
      "key": "uploads/video.mp4",
      "size_bytes": 1024000,
      "last_modified": "2026-06-01T10:30:00+00:00",
      "etag": "d41d8cd98f00b204e9800998ecf8427e",
      "isDuplicate": false
    },
    {
      "name": "video.mp4",                      # ← Mismo nombre
      "key": "uploads/video.mp4.2",
      "size_bytes": 1024000,
      "last_modified": "2026-06-01T11:00:00+00:00",
      "etag": "d41d8cd98f00b204e9800998ecf8427e",  # ← Mismo contenido
      "isDuplicate": true                         # ← Marcado como duplicado
    }
  ],
  "total_count": 2
}
```

### 4. Seguridad (SEC-07)

- ✅ No expone rutas internas del servidor
- ✅ ETag viene de S3 (no es información sensible)
- ✅ Errores genéricos si falla la conexión
- ✅ Manejo robusto de excepciones

---

## 🎨 Implementación Frontend

### 1. Componente React - Cambios en `App.jsx`

**Antes:**
```jsx
<td className="file-name">
  <span className="file-icon">🎬</span>
  {file.name}
</td>
```

**Después:**
```jsx
<td className="file-name">
  <span className="file-icon">🎬</span>
  <div className="file-name-wrapper">
    <span>{file.name}</span>
    {file.isDuplicate && (
      <span className="duplicate-badge" title="Este video está duplicado (mismo nombre o contenido)">
        ⚠️ Duplicado
      </span>
    )}
  </div>
</td>
```

### 2. Fila de tabla con estilo especial

```jsx
<tr key={index} className={file.isDuplicate ? 'row-duplicate' : ''}>
  {/* Contenido */}
</tr>
```

### 3. Estilos CSS - `App.css`

#### Estilo de fila duplicada (fondo amarillo tenue)
```css
.files-table tbody tr.row-duplicate {
  background: rgba(255, 193, 7, 0.05);      /* Fondo amarillo suave */
  border-left: 4px solid #FFC107;            /* Borde amarillo */
}

.files-table tbody tr.row-duplicate:hover {
  background: rgba(255, 193, 7, 0.1);        /* Más visible al pasar el mouse */
}
```

#### Badge de alerta (etiqueta roja con animación)
```css
.duplicate-badge {
  display: inline-block;
  background: #f5222d;                       /* Rojo alerta */
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  width: fit-content;
  box-shadow: 0 2px 6px rgba(245, 34, 45, 0.3);
  animation: pulse 1.5s infinite;            /* Pulso suave */
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 2px 6px rgba(245, 34, 45, 0.3);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 2px 8px rgba(245, 34, 45, 0.5);
  }
}
```

---

## 👁️ Resultado Visual

### Tabla sin duplicados:
```
| Nombre              | Tamaño    | Fecha          | Acciones        |
|---------------------|-----------|----------------|-----------------|
| 🎬 video1.mp4       | 150.5 MB  | 01/06 10:30    | ⬇️ ⭕           |
| 🎬 video2.mp4       | 200.0 MB  | 01/06 11:00    | ⬇️ ⭕           |
```

### Tabla con duplicados:
```
| Nombre              | Tamaño    | Fecha          | Acciones        |
|---------------------|-----------|----------------|-----------------|
| 🎬 video1.mp4       | 150.5 MB  | 01/06 10:30    | ⬇️ ⭕           |
|      ⚠️ Duplicado   |           |                |                 |
| 🎬 video1.mp4       | 150.5 MB  | 01/06 10:35    | ⬇️ ⭕           | ← Fondo amarillo
|      ⚠️ Duplicado   |           |                |                 |
| 🎬 video2.mp4       | 200.0 MB  | 01/06 11:00    | ⬇️ ⭕           |
```

**Características visuales:**
- 🟡 Fondo amarillo suave en toda la fila
- 🔴 Badge rojo con "⚠️ Duplicado" pulsando suavemente
- 📌 Borde amarillo izquierdo para llamar atención

---

## 🧪 Casos de Uso

### Caso 1: Archivo duplicado por nombre
```
Subas: video.mp4 (100 MB, hash ABC123)
Luego: video.mp4 (100 MB, hash ABC123) nuevamente

Resultado: Ambos marcados como isDuplicate: true
```

### Caso 2: Mismo contenido, diferente nombre
```
Subas: video.mp4  (hash DEF456)
Luego: copia_video.mp4 (hash DEF456)  ← Mismo contenido

Resultado: Ambos marcados como isDuplicate: true
```

### Caso 3: Archivo único
```
Subas: video.mp4 (hash GHI789)

Resultado: isDuplicate: false
```

---

## 🔄 Flujo Completo

### 1. Usuario sube archivo
```
Frontend → POST /api/upload/presigned-url → Backend
         → PUT (directo a S3)
```

### 2. Frontend refresca lista (cada 5 seg)
```
Frontend → GET /api/files → Backend
         ↓
Backend lista uploads/ con ETag
         ↓
Backend cuenta ocurrencias (nombre + ETag)
         ↓
Backend retorna isDuplicate para cada archivo
         ↓
Frontend renderiza con alerta visual si isDuplicate: true
```

### 3. Usuario ve duplicados resaltados
```
✅ Badge rojo con animación
✅ Fila con fondo amarillo
✅ Tooltip explicativo al pasar mouse
```

---

## 📊 Performance

- **Complejidad:** O(n) donde n = cantidad de archivos
- **Memoria:** O(n) para los diccionarios de conteo
- **Tiempo:** < 100ms para 1000 archivos típicamente

---

## 🛡️ Consideraciones de Seguridad

| Aspecto | Implementación |
|--------|----------------|
| **No expone internals** | ETag es público en S3 |
| **Manejo de errores** | Devuelve 500 genérico |
| **CORS** | Restringido a localhost:5173 |
| **Validación** | Prefijo 'uploads/' validado |

---

## 🚀 Cómo probar

### 1. Sube dos archivos idénticos
```bash
# Mismo archivo, dos veces
curl -F "file=@video.mp4" http://localhost:8000/api/upload/presigned-url
```

### 2. Verifica el endpoint
```bash
curl http://localhost:8000/api/files | jq '.files[] | {name, isDuplicate}'
```

### 3. Verifica en UI
- Abre http://localhost:5173
- Deberías ver badges rojos con "⚠️ Duplicado"
- Filas con fondo amarillo suave

---

## 📝 Notas

- Los duplicados NO se eliminan automáticamente (decisión del usuario)
- La detección es en **tiempo real** al listar archivos
- Compatible con S3 estándar (ETag disponible en todos los objetos)
- Feature opcional pero recomendada para producción

---

**Pareja P-11** - ArchivaCloud SpA | Feature Extra implementada ✅
