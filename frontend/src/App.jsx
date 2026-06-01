import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

const BACKEND_URL = 'http://localhost:8000'
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100 MB
const ALLOWED_EXTENSIONS = ['.mp4', '.mov']

function App() {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const fileInputRef = useRef(null)

  // Cargar lista de archivos al montar el componente
  useEffect(() => {
    fetchFiles()
    const interval = setInterval(fetchFiles, 5000) // Refrescar cada 5 segundos
    return () => clearInterval(interval)
  }, [])

  // Obtener lista de archivos del backend
  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/files`)
      setFiles(response.data.files)
      setError('')
    } catch (err) {
      console.error('Error al obtener archivos:', err)
      setError('No se pudo conectar con el servidor.')
    }
  }

  // Validar archivo
  const validateFile = (file) => {
    // Validar extensión
    const extension = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError(`❌ Solo se permiten archivos .mp4 o .mov. Recibido: ${extension}`)
      return false
    }

    // Validar tamaño
    if (file.size > MAX_FILE_SIZE) {
      setError(`❌ El archivo excede 100 MB. Tamaño: ${(file.size / 1024 / 1024).toFixed(2)} MB`)
      return false
    }

    return true
  }

  // Manejo de selección de archivo
  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!validateFile(file)) {
      fileInputRef.current.value = ''
      return
    }

    setError('')
    setSuccess('')
    setUploading(true)
    setUploadProgress(0)

    try {
      // Paso 1: Obtener Presigned URL del backend
      const fileName = file.name
      const fileType = fileName.split('.').pop()

      const presignedResponse = await axios.post(
        `${BACKEND_URL}/api/upload/presigned-url`,
        { fileName, fileType }
      )

      const { presignedUrl, key, publicUrl } = presignedResponse.data

      // Paso 2: Subir directamente a S3 con progreso
      await axios.put(presignedUrl, file, {
        headers: {
          'Content-Type': file.type,
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          setUploadProgress(percentCompleted)
        },
      })

      setSuccess(`✅ Archivo subido exitosamente: ${fileName}`)
      setUploadProgress(0)
      fileInputRef.current.value = ''

      // Refrescar lista de archivos
      setTimeout(() => fetchFiles(), 1000)
    } catch (err) {
      console.error('Error en la subida:', err)
      setError('❌ Error al subir el archivo. Intenta nuevamente.')
      setUploadProgress(0)
    } finally {
      setUploading(false)
    }
  }

  // Descargar archivo desde S3
  const handleDownload = (file) => {
    window.open(file.key, '_blank')
  }

  // Eliminar archivo con confirmación
  const handleDelete = async (key) => {
    if (!window.confirm(`¿Estás seguro de que deseas eliminar "${key}"?`)) {
      return
    }

    try {
      await axios.delete(`${BACKEND_URL}/api/files/${key}`)
      setSuccess(`✅ Archivo eliminado exitosamente`)
      setError('')
      setTimeout(() => fetchFiles(), 500)
    } catch (err) {
      console.error('Error al eliminar:', err)
      setError('❌ Error al eliminar el archivo.')
    }
  }

  // Formatear tamaño de archivo
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  // Formatear fecha
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🎬 ArchivaCloud</h1>
        <p className="subtitle">Gestor de Videos Seguro en Cloud</p>
      </header>

      <main className="app-main">
        {/* Sección de Carga */}
        <section className="upload-section">
          <div className="upload-card">
            <h2>📤 Subir Archivo</h2>
            
            <div className="upload-input-wrapper">
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.mov"
                onChange={handleFileSelect}
                disabled={uploading}
                className="file-input"
                id="file-input"
              />
              <label htmlFor="file-input" className={`upload-button ${uploading ? 'disabled' : ''}`}>
                {uploading ? '⏳ Subiendo...' : '📁 Seleccionar Archivo'}
              </label>
            </div>

            <p className="upload-hint">
              ✓ Formatos: .mp4, .mov | ✓ Máximo: 100 MB | SEC-04 / CU-05
            </p>

            {/* Barra de Progreso - CU-01 */}
            {uploading && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="progress-text">{uploadProgress}% completado</p>
              </div>
            )}

            {/* Mensajes */}
            {error && <div className="alert alert-error">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}
          </div>
        </section>

        {/* Sección de Listado - CU-02 */}
        <section className="files-section">
          <div className="files-card">
            <h2>📹 Videos Subidos</h2>
            
            {files.length === 0 ? (
              <div className="empty-state">
                <p>No hay videos aún. ¡Sube tu primer video!</p>
              </div>
            ) : (
              <div className="files-table-wrapper">
                <table className="files-table">
                  <thead>
                    <tr>
                      <th>Nombre del Archivo</th>
                      <th>Tamaño</th>
                      <th>Fecha de Subida</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file, index) => (
                      <tr key={index} className={file.isDuplicate ? 'row-duplicate' : ''}>
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
                        <td>{formatFileSize(file.size_bytes)}</td>
                        <td>{formatDate(file.last_modified)}</td>
                        <td className="actions-cell">
                          <button
                            onClick={() => handleDownload(file)}
                            className="action-btn download-btn"
                            title="Descargar desde S3"
                          >
                            ⬇️ Descargar
                          </button>
                          <button
                            onClick={() => handleDelete(file.key)}
                            className="action-btn delete-btn"
                            title="Eliminar archivo"
                          >
                            🗑️ Eliminar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <p className="table-hint">
              CU-02 (Listar) | CU-03 (Descargar) | CU-04 (Eliminar) | Auto-refresca cada 5s
            </p>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <p>ArchivaCloud SpA - Pareja P-11 | Backend: {BACKEND_URL}</p>
      </footer>
    </div>
  )
}

export default App
