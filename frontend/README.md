# ArchivaCloud Frontend - React + Vite

Interfaz de usuario moderna para el gestor de videos en la nube ArchivaCloud.

## Requisitos

- **Node.js** v16+ ([Descargar](https://nodejs.org/))
- **npm** v8+ (viene incluido con Node.js)

## Instalación

### 1. Instalar Node.js (si no lo tienes)

Descarga e instala desde: https://nodejs.org/ (LTS recomendado)

### 2. Instalar dependencias

```bash
cd frontend
npm install
```

## Desarrollo

```bash
npm run dev
```

La aplicación se abrirá automáticamente en `http://localhost:5173`

## Características Implementadas

✅ **Selección de archivos** (CU-05 / SEC-04)
- Validación cliente: Solo .mp4 y .mov
- Máximo 100 MB
- Mensajes de error informativos

✅ **Barra de progreso** (CU-01)
- Progreso real de carga a S3
- Indicador de porcentaje

✅ **Listado de videos** (CU-02)
- Tabla con nombre, tamaño y fecha
- Auto-refresco cada 5 segundos
- Información formateada y legible

✅ **Descargar** (CU-03)
- Abre archivo desde S3 en nueva pestaña

✅ **Eliminar** (CU-04)
- Confirmación antes de borrar
- Actualización automática de lista

✅ **Diseño Responsivo**
- Mobile-first
- Funciona en desktop, tablet y móvil
- Estilos modernos con gradientes

## Stack Tecnológico

- **React 18** - Framework UI
- **Vite** - Build tool
- **Axios** - Cliente HTTP
- **CSS3** - Estilos modernos

## Conexión Backend

El frontend se conecta automáticamente al backend en:
```
http://localhost:8000
```

Asegúrate de que el backend esté ejecutándose antes de usar la aplicación.

## Build para Producción

```bash
npm run build
npm run preview
```

## Estructura de Carpetas

```
frontend/
├── src/
│   ├── App.jsx        # Componente principal
│   ├── App.css        # Estilos
│   ├── index.css      # Estilos globales
│   └── main.jsx       # Entrada
├── index.html         # HTML principal
├── package.json       # Dependencias
├── vite.config.js     # Config Vite
└── README.md          # Este archivo
```

## Notas de Seguridad

- El frontend NO almacena credenciales
- Las URLs presignadas se obtienen del backend
- La carga directa a S3 usa URLs temporales
- CORS está configurado en el backend

---

**Pareja P-11** - ArchivaCloud SpA
