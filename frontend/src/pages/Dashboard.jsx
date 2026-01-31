import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { getDocuments, uploadDocument, deleteDocument } from '../services/api'
import {
    Upload, FileText, Music, Video, Trash2, MessageSquare,
    Clock, AlertCircle, CheckCircle, Loader
} from 'lucide-react'
import './Dashboard.css'

const documentTypeIcons = {
    pdf: FileText,
    audio: Music,
    video: Video
}

const statusColors = {
    pending: 'var(--color-warning)',
    processing: 'var(--color-info)',
    completed: 'var(--color-success)',
    failed: 'var(--color-error)'
}

export default function Dashboard() {
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState('')
    const [uploadProgress, setUploadProgress] = useState({})

    useEffect(() => {
        loadDocuments()
    }, [])

    // Poll for updates when documents are processing
    useEffect(() => {
        const hasProcessing = documents.some(
            doc => doc.status === 'processing' || doc.status === 'pending'
        )

        if (hasProcessing) {
            const interval = setInterval(() => {
                loadDocuments()
            }, 3000) // Poll every 3 seconds

            return () => clearInterval(interval)
        }
    }, [documents])

    async function loadDocuments() {
        try {
            const data = await getDocuments()
            setDocuments(data.documents)
        } catch (err) {
            setError('Failed to load documents')
        } finally {
            setLoading(false)
        }
    }

    const onDrop = useCallback(async (acceptedFiles) => {
        setUploading(true)
        setError('')

        for (const file of acceptedFiles) {
            const fileId = Date.now()
            setUploadProgress(prev => ({
                ...prev,
                [fileId]: { name: file.name, progress: 0, status: 'uploading' }
            }))

            try {
                // Determine file type
                let type = 'pdf'
                if (file.type.startsWith('audio/')) type = 'audio'
                else if (file.type.startsWith('video/')) type = 'video'
                else if (file.name.match(/\.(mp3|wav|m4a|flac|ogg)$/i)) type = 'audio'
                else if (file.name.match(/\.(mp4|webm|mkv|avi|mov)$/i)) type = 'video'

                await uploadDocument(file, type)

                setUploadProgress(prev => ({
                    ...prev,
                    [fileId]: { ...prev[fileId], progress: 100, status: 'completed' }
                }))

                // Refresh documents list
                await loadDocuments()
            } catch (err) {
                setUploadProgress(prev => ({
                    ...prev,
                    [fileId]: { ...prev[fileId], status: 'failed', error: err.message }
                }))
            }
        }

        setUploading(false)
    }, [])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg'],
            'video/*': ['.mp4', '.webm', '.mkv', '.avi', '.mov']
        },
        maxSize: 100 * 1024 * 1024 // 100MB
    })

    async function handleDelete(docId) {
        if (!confirm('Are you sure you want to delete this document?')) return

        try {
            await deleteDocument(docId)
            setDocuments(prev => prev.filter(d => d.id !== docId))
        } catch (err) {
            setError('Failed to delete document')
        }
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        })
    }

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h1>Your Documents</h1>
                <p>Upload and manage your documents for AI-powered Q&A</p>
            </div>

            {/* Upload Zone */}
            <div
                {...getRootProps()}
                className={`upload-zone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
            >
                <input {...getInputProps()} />
                <Upload size={48} className="upload-icon" />
                <h3>
                    {isDragActive
                        ? 'Drop your files here'
                        : 'Drag & drop files here'}
                </h3>
                <p>or click to browse your computer</p>
                <div className="upload-formats">
                    <span><FileText size={16} /> PDF</span>
                    <span><Music size={16} /> Audio</span>
                    <span><Video size={16} /> Video</span>
                </div>
            </div>

            {/* Upload Progress */}
            {Object.keys(uploadProgress).length > 0 && (
                <div className="upload-progress-list">
                    {Object.entries(uploadProgress).map(([id, item]) => (
                        <div key={id} className={`upload-progress-item ${item.status}`}>
                            {item.status === 'uploading' && <Loader size={16} className="animate-spin" />}
                            {item.status === 'completed' && <CheckCircle size={16} />}
                            {item.status === 'failed' && <AlertCircle size={16} />}
                            <span className="upload-filename">{item.name}</span>
                            <span className="upload-status">{item.status}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="dashboard-error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                </div>
            )}

            {/* Documents List */}
            <div className="documents-section">
                <h2>Recent Documents</h2>

                {loading ? (
                    <div className="documents-loading">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="document-skeleton skeleton" />
                        ))}
                    </div>
                ) : documents.length === 0 ? (
                    <div className="documents-empty">
                        <FileText size={48} />
                        <h3>No documents yet</h3>
                        <p>Upload your first document to get started</p>
                    </div>
                ) : (
                    <div className="documents-grid">
                        {documents.map(doc => {
                            const Icon = documentTypeIcons[doc.document_type] || FileText

                            return (
                                <div key={doc.id} className="document-card card">
                                    <div className="document-icon">
                                        <Icon size={24} />
                                    </div>

                                    <div className="document-info">
                                        <h4>{doc.original_filename}</h4>
                                        <div className="document-meta">
                                            <span>{formatFileSize(doc.file_size)}</span>
                                            <span>•</span>
                                            <span>{formatDate(doc.created_at)}</span>
                                        </div>
                                    </div>

                                    <div
                                        className="document-status"
                                        style={{ color: statusColors[doc.status] }}
                                    >
                                        {doc.status === 'processing' && <Loader size={14} className="animate-spin" />}
                                        {doc.status === 'completed' && <CheckCircle size={14} />}
                                        {doc.status === 'pending' && <Clock size={14} />}
                                        {doc.status === 'failed' && <AlertCircle size={14} />}
                                        <span>{doc.status}</span>
                                    </div>

                                    <div className="document-actions">
                                        {doc.status === 'completed' && (
                                            <Link
                                                to={`/chat/${doc.id}`}
                                                className="btn btn-primary btn-sm"
                                            >
                                                <MessageSquare size={16} />
                                                Chat
                                            </Link>
                                        )}
                                        <button
                                            onClick={() => handleDelete(doc.id)}
                                            className="btn btn-ghost btn-icon"
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}
