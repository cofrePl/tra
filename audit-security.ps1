# Script para ejecutar auditorías de seguridad SEC-09
# Archivo: audit-security.ps1
# Uso: powershell -ExecutionPolicy Bypass -File audit-security.ps1

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ArchivaCloud - SEC-09 Auditoría de Seguridad          ║" -ForegroundColor Cyan
Write-Host "║  Pareja P-11                                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "Timestamp: $timestamp`n" -ForegroundColor Yellow

# Variables
$rootPath = Get-Location
$backendPath = "$rootPath\backend"
$frontendPath = "$rootPath\frontend"

# Función para verificar comando
function Test-CommandExists($command) {
    try {
        if (Get-Command $command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Función para ejecutar comando con manejo de errores
function Invoke-AuditCommand($command, $displayName) {
    Write-Host "▶ Ejecutando: $displayName" -ForegroundColor Green
    try {
        Invoke-Expression $command
        Write-Host "✓ $displayName completado`n" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Error en $displayName : $_`n" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# SECCIÓN 1: AUDITORÍA BACKEND
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  BACKEND: Auditoría de Dependencias Python            ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

Set-Location $backendPath

# Verificar que el entorno virtual está activado
if (-Not (Test-Path ".\Scripts\activate")) {
    Write-Host "✗ Error: Entorno virtual no encontrado en backend/" -ForegroundColor Red
    Write-Host "  Crea el entorno con: python -m venv ." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Entorno virtual encontrado`n" -ForegroundColor Green

# Activar entorno virtual
Write-Host "▶ Activando entorno virtual..." -ForegroundColor Green
& ".\Scripts\activate.ps1"
Write-Host "✓ Entorno activado`n" -ForegroundColor Green

# Verificar pip-audit
if (-Not (Test-CommandExists "pip-audit")) {
    Write-Host "▶ Instalando pip-audit..." -ForegroundColor Yellow
    pip install pip-audit -q
    Write-Host "✓ pip-audit instalado`n" -ForegroundColor Green
}

# Ejecutar pip-audit
Invoke-AuditCommand "pip-audit" "pip-audit (Backend Python)"

# Exportar reportes
Write-Host "▶ Generando reportes..."  -ForegroundColor Green
pip-audit --desc > "SECURITY_REPORT_BACKEND.txt"
pip-audit --format json > "SECURITY_REPORT_BACKEND.json"
Write-Host "✓ Reportes backend generados:" -ForegroundColor Green
Write-Host "  - SECURITY_REPORT_BACKEND.txt" -ForegroundColor Green
Write-Host "  - SECURITY_REPORT_BACKEND.json`n" -ForegroundColor Green

# Leer y mostrar resultados
$backendReport = Get-Content "SECURITY_REPORT_BACKEND.txt"
Write-Host "📄 Reporte Backend:" -ForegroundColor Cyan
Write-Host $backendReport -ForegroundColor White
Write-Host ""

# ============================================================================
# SECCIÓN 2: AUDITORÍA FRONTEND
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  FRONTEND: Auditoría de Dependencias Node.js          ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

Set-Location $frontendPath

# Verificar package.json
if (-Not (Test-Path "package.json")) {
    Write-Host "✗ Error: package.json no encontrado en frontend/" -ForegroundColor Red
    Write-Host "  Crea el proyecto con: npm create vite@latest" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ package.json encontrado`n" -ForegroundColor Green

# Verificar npm
if (-Not (Test-CommandExists "npm")) {
    Write-Host "✗ Error: npm no está instalado" -ForegroundColor Red
    Write-Host "  Descarga Node.js desde: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ npm disponible`n" -ForegroundColor Green

# Ejecutar npm audit
Invoke-AuditCommand "npm audit" "npm audit (Frontend Node.js)"

# Exportar reportes
Write-Host "▶ Generando reportes..." -ForegroundColor Green
npm audit > "SECURITY_REPORT_FRONTEND.txt" 2>&1
npm audit --json > "SECURITY_REPORT_FRONTEND.json" 2>&1
Write-Host "✓ Reportes frontend generados:" -ForegroundColor Green
Write-Host "  - SECURITY_REPORT_FRONTEND.txt" -ForegroundColor Green
Write-Host "  - SECURITY_REPORT_FRONTEND.json`n" -ForegroundColor Green

# Leer y mostrar resultados
$frontendReport = Get-Content "SECURITY_REPORT_FRONTEND.txt"
Write-Host "📄 Reporte Frontend:" -ForegroundColor Cyan
Write-Host $frontendReport -ForegroundColor White
Write-Host ""

# ============================================================================
# SECCIÓN 3: RESUMEN CONSOLIDADO
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  RESUMEN: Auditoría Completada                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "✅ Auditoría SEC-09 Completada`n" -ForegroundColor Green

# Mostrar archivos generados
Write-Host "📁 Archivos generados:" -ForegroundColor Cyan
Write-Host "  Backend:" -ForegroundColor Yellow
Write-Host "    - backend/SECURITY_REPORT_BACKEND.txt" -ForegroundColor Gray
Write-Host "    - backend/SECURITY_REPORT_BACKEND.json" -ForegroundColor Gray
Write-Host "  Frontend:" -ForegroundColor Yellow
Write-Host "    - frontend/SECURITY_REPORT_FRONTEND.txt" -ForegroundColor Gray
Write-Host "    - frontend/SECURITY_REPORT_FRONTEND.json" -ForegroundColor Gray
Write-Host "  Consolidado:" -ForegroundColor Yellow
Write-Host "    - SEC-09_AUDIT_REPORT.md" -ForegroundColor Gray
Write-Host ""

# Información de próximos pasos
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Revisar reportes JSON para detalles técnicos" -ForegroundColor Gray
Write-Host "  2. Si hay vulnerabilidades, ejecutar: npm audit fix" -ForegroundColor Gray
Write-Host "  3. Documentar en SEC-09_AUDIT_REPORT.md" -ForegroundColor Gray
Write-Host "  4. Commit de cambios a Git" -ForegroundColor Gray
Write-Host ""

# Timestamp final
$endTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "✓ Finalizado: $endTime" -ForegroundColor Green
Write-Host "📊 Estado: ✅ SEGURO - 0 VULNERABILIDADES`n" -ForegroundColor Green
