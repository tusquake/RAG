import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

// Create axios instance
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// Auth API
export async function login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    return response.data
}

export async function register(email, password, name) {
    const response = await api.post('/auth/register', { email, password, name })
    return response.data
}

export async function getCurrentUser(token) {
    const response = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
}

// Document API
export async function uploadDocument(file, type) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post(`/upload/${type}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
}

export async function getDocuments(page = 1, pageSize = 10) {
    const response = await api.get('/documents', {
        params: { page, page_size: pageSize }
    })
    return response.data
}

export async function getDocument(documentId) {
    const response = await api.get(`/documents/${documentId}`)
    return response.data
}

export async function deleteDocument(documentId) {
    await api.delete(`/documents/${documentId}`)
}

export function getDocumentFileUrl(documentId) {
    const token = localStorage.getItem('token')
    return `${API_URL}/documents/${documentId}/file?token=${token}`
}

// Chat API
export async function sendMessage(documentId, message) {
    const response = await api.post('/chat', {
        document_id: documentId,
        message: message
    })
    return response.data
}

export async function streamMessage(documentId, message, onChunk) {
    const token = localStorage.getItem('token')

    const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            document_id: documentId,
            message: message,
            stream: true
        })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6))
                    onChunk(data)
                } catch (e) {
                    console.error('Failed to parse SSE data:', e)
                }
            }
        }
    }
}

export async function getChatHistory(documentId) {
    const response = await api.get(`/chat/history/${documentId}`)
    return response.data
}

export async function summarizeDocument(documentId, maxLength = 500) {
    const response = await api.post('/chat/summarize', {
        document_id: documentId,
        max_length: maxLength
    })
    return response.data
}

export async function findTimestamps(documentId, query) {
    const response = await api.post('/chat/timestamps', {
        document_id: documentId,
        query: query
    })
    return response.data
}

export default api
