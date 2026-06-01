import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

const BACKEND_URL = 'http://localhost:8000'
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100 MB
const ALLOWED_EXTENSIONS = ['.mp4', '.mov']
const S3_BASE_URL = 'https://archivacloud-p11.s3.us-west-2.amazonaws.com'

function App() {
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/files`)
      setFiles(response.data)
      setErrorMessage('')
    } catch (error) {
      console.error('Error al obtener archivos:', error)
      setErrorMessage('No se pudo cargar la lista de archivos. Intenta de nuevo.')
    }
  }

  const validateFile = (file) => {
    const extension = '.' + file.name.split('.').pop().toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setErrorMessage('❌ Solo se permiten archivos .mp4 o .mov.')
      return false
    }

    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage(`❌ El archivo excede 100 MB. Tamaño: ${(file.size / 1024 / 1024).toFixed(2)} MB`)
      return false
    }

    return true
  }

  const handleFileChange = (event) => {
    const file = event.target.files?.[0]
    if (!file) {
      setSelectedFile(null)
      return
    }

    if (!validateFile(file)) {
      setSelectedFile(null)
      event.target.value = ''
      return
    }

    setSelectedFile(file)
    setErrorMessage('')
    setSuccessMessage('')
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage('Selecciona primero un archivo válido antes de subir.')
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setErrorMessage('')
    setSuccessMessage('')

    try {
      const fileName = selectedFile.name
      const fileType = fileName.split('.').pop()

      const presignedResponse = await axios.post(`${BACKEND_URL}/api/upload/presigned-url`, {
        fileName,
        fileType,
      })

      const { presignedUrl } = presignedResponse.data

      await axios.put(presignedUrl, selectedFile, {
        headers: { 'Content-Type': selectedFile.type },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(percentCompleted)
        },
      })

      setSuccessMessage(`✅ Archivo subido exitosamente: ${fileName}`)
      setSelectedFile(null)
      fileInputRef.current.value = ''
      await fetchFiles()
    } catch (error) {
      console.error('Error en la subida:', error)
      setErrorMessage('❌ Error al subir el archivo. Intenta nuevamente.')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDelete = async (key) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este archivo?')) {
      return
    }

    try {
      await axios.delete(`${BACKEND_URL}/api/files/${encodeURIComponent(key)}`)
      setSuccessMessage('✅ Archivo eliminado exitosamente.')
      setErrorMessage('')
      await fetchFiles()
    } catch (error) {
      console.error('Error al eliminar:', error)
      setErrorMessage('❌ No se pudo eliminar el archivo. Intenta nuevamente.')
    }
  }

  const formatFileSizeMB = (bytes) => `${(bytes / 1024 / 1024).toFixed(2)} MB`

  const formatDate = (dateString) =>
    new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🎬 ArchivaCloud</h1>
        <p className="subtitle">Gestor de videos para P-11 conectado a localhost</p>
      </header>

      <main className="app-main">
        <section className="upload-section">
          <div className="upload-card">
            <h2>📤 Subir video</h2>

            <div className="upload-input-wrapper">
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.mov"
                onChange={handleFileChange}
                disabled={uploading}
                className="file-input"
                id="file-input"
              />
              <label htmlFor="file-input" className={`upload-button ${uploading ? 'disabled' : ''}`}>
                {uploading ? '⏳ Seleccionando...' : '📁 Seleccionar archivo'}
              </label>
            </div>

            <button
              className="upload-button"
              type="button"
              onClick={handleUpload}
              disabled={uploading || !selectedFile}
              style={{ marginTop: '1rem' }}
            >
              {uploading ? '⏳ Subiendo...' : '🚀 Iniciar subida'}
            </button>

            <p className="upload-hint">Formados permitidos: .mp4, .mov · Máximo 100 MB</p>

            {uploading && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
                </div>
                <p className="progress-text">{uploadProgress}% completado</p>
              </div>
            )}

            {errorMessage && <div className="alert alert-error">{errorMessage}</div>}
            {successMessage && <div className="alert alert-success">{successMessage}</div>}
          </div>
        </section>

        <section className="files-section">
          <div className="files-card">
            <h2>📹 Videos subidos</h2>

            {files.length === 0 ? (
              <div className="empty-state">
                <p>No hay videos aún. Sube tu primer video.</p>
              </div>
            ) : (
              <div className="files-table-wrapper">
                <table className="files-table">
                  <thead>
                    <tr>
                      <th>Nombre del archivo</th>
                      <th>Tamaño</th>
                      <th>Fecha</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file) => (
                      <tr key={file.key}>
                        <td className="file-name">
                          <span className="file-icon">🎬</span>
                          <div className="file-name-wrapper">
                            <span>{file.name}</span>
                            {file.isDuplicate && (
                              <span className="duplicate-badge" title="Duplicado por mismo nombre o mismo contenido">
                                ⚠️ Duplicado (Mismo nombre o contenido)
                              </span>
                            )}
                          </div>
                        </td>
                        <td>{formatFileSizeMB(file.size)}</td>
                        <td>{formatDate(file.lastModified)}</td>
                        <td className="actions-cell">
                          <a
                            href={`${S3_BASE_URL}/${encodeURIComponent(file.key)}`}
                            target="_blank"
                            rel="noreferrer"
                            className="action-btn download-btn"
                          >
                            Abrir/Descargar
                          </a>
                          <button
                            className="action-btn delete-btn"
                            type="button"
                            onClick={() => handleDelete(file.key)}
                          >
                            Eliminar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
