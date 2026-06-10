import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

const BACKEND_URL = 'http://localhost:8000'
const MAX_FILE_SIZE = 100 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['.mp4', '.mov']

function App() {
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [message, setMessage] = useState({ text: '', type: '' })
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/files`)
      setFiles(response.data)
      setMessage({ text: '', type: '' })
    } catch (error) {
      setMessage({ text: 'Error al cargar archivos. Intenta de nuevo.', type: 'error' })
    }
  }

  const validateFile = (file) => {
    const extension = `.${file.name.split('.').pop().toLowerCase()}`
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setMessage({ text: 'Solo se permiten archivos .mp4 y .mov.', type: 'error' })
      return false
    }

    if (file.size > MAX_FILE_SIZE) {
      setMessage({ text: `El archivo excede 100 MB. Tamaño: ${(file.size / 1024 / 1024).toFixed(2)} MB`, type: 'error' })
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
    setMessage({ text: '', type: '' })
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage({ text: 'Selecciona primero un archivo válido antes de subir.', type: 'error' })
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setMessage({ text: '', type: '' })

    try {
      const fileName = selectedFile.name
      const fileType = fileName.split('.').pop()

      const presignedResponse = await axios.post(`${BACKEND_URL}/api/upload/presigned-url`, {
        fileName,
        fileType,
        fileSize: selectedFile.size,
      })

      const { presignedUrl } = presignedResponse.data

      await axios.put(presignedUrl, selectedFile, {
        headers: { 'Content-Type': selectedFile.type },
        onUploadProgress: (event) => {
          if (event.total) {
            setUploadProgress(Math.round((event.loaded * 100) / event.total))
          }
        },
      })

      setMessage({ text: `Archivo subido exitosamente: ${fileName}`, type: 'success' })
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      await fetchFiles()
    } catch (error) {
      setMessage({ text: 'Error al subir el archivo. Intenta nuevamente.', type: 'error' })
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleOpen = (fileUrl) => {
    if (!fileUrl) {
      setMessage({ text: 'No se pudo abrir el archivo. URL inválida.', type: 'error' })
      return
    }

    window.open(fileUrl, '_blank')
  }

  const handleDelete = async (key) => {
    if (!window.confirm('¿Estás seguro que deseas eliminar este archivo?')) return

    try {
      await axios.delete(`${BACKEND_URL}/api/files/${encodeURIComponent(key)}`)
      setMessage({ text: 'Archivo eliminado exitosamente.', type: 'success' })
      await fetchFiles()
    } catch (error) {
      setMessage({ text: 'No se pudo eliminar el archivo. Intenta nuevamente.', type: 'error' })
    }
  }

  const formatSize = (bytes) => `${(bytes / 1024 / 1024).toFixed(2)} MB`
  const formatDate = (date) => new Date(date).toLocaleString('es-ES', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>ArchivaCloud</h1>
        <p>Sube videos .mp4 / .mov a S3 usando URL firmadas.</p>
      </header>

      <section className="upload-panel">
        <div className="card">
          <h2>Subir archivo</h2>
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp4,.mov"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <button onClick={handleUpload} disabled={uploading || !selectedFile}>
            {uploading ? 'Subiendo...' : 'Subir archivo'}
          </button>
          <p className="hint">Máximo 100 MB. Solo .mp4 y .mov.</p>

          {uploading && (
            <div className="progress-wrapper">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
              </div>
              <span>{uploadProgress}%</span>
            </div>
          )}

          {message.text && (
            <div className={`message ${message.type === 'error' ? 'error' : 'success'}`}>
              {message.text}
            </div>
          )}
        </div>
      </section>

      <section className="files-panel">
        <div className="card">
          <h2>Archivos en el bucket</h2>

          {files.length === 0 ? (
            <p>No hay archivos cargados aún.</p>
          ) : (
            <table className="files-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Tamaño</th>
                  <th>Fecha</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.key} className={file.isDuplicate ? 'duplicate-row' : ''}>
                    <td>
                      {file.name}
                    </td>
                    <td>{formatSize(file.size)}</td>
                    <td>{formatDate(file.lastModified)}</td>
                    <td>
                      <button onClick={() => handleOpen(file.url)} style={{ marginRight: '10px' }}>
                        Abrir
                      </button>
                      <button onClick={() => handleDelete(file.key)}>
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  )
}

export default App
