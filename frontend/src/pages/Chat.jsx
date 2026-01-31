import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import {
    getDocument, getChatHistory, sendMessage, streamMessage,
    summarizeDocument, getDocumentFileUrl
} from '../services/api'
import MediaPlayer from '../components/Media/MediaPlayer'
import {
    ArrowLeft, Send, Loader, FileText, Clock,
    Sparkles, User, Bot, Play
} from 'lucide-react'
import './Chat.css'

export default function Chat() {
    const { documentId } = useParams()
    const [document, setDocument] = useState(null)
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(true)
    const [sending, setSending] = useState(false)
    const [summary, setSummary] = useState('')
    const [summarizing, setSummarizing] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const messagesEndRef = useRef(null)
    const playerRef = useRef(null)

    useEffect(() => {
        loadDocumentAndHistory()
    }, [documentId])

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    async function loadDocumentAndHistory() {
        try {
            const [docData, historyData] = await Promise.all([
                getDocument(documentId),
                getChatHistory(documentId)
            ])

            setDocument(docData)
            setMessages(historyData.messages || [])

            if (docData.summary) {
                setSummary(docData.summary)
            }
        } catch (err) {
            console.error('Failed to load document:', err)
        } finally {
            setLoading(false)
        }
    }

    function scrollToBottom() {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    async function handleSubmit(e) {
        e.preventDefault()
        if (!input.trim() || sending) return

        const userMessage = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev, userMessage])
        setInput('')
        setSending(true)

        // Add placeholder for assistant response
        const placeholderId = Date.now()
        setMessages(prev => [...prev, {
            id: placeholderId,
            role: 'assistant',
            content: '',
            isStreaming: true
        }])

        try {
            let fullResponse = ''
            let timestamps = []

            await streamMessage(documentId, userMessage.content, (data) => {
                if (data.content) {
                    fullResponse += data.content
                    setMessages(prev => prev.map(msg =>
                        msg.id === placeholderId
                            ? { ...msg, content: fullResponse }
                            : msg
                    ))
                }

                if (data.done) {
                    timestamps = data.timestamps || []
                    setMessages(prev => prev.map(msg =>
                        msg.id === placeholderId
                            ? { ...msg, isStreaming: false, timestamps }
                            : msg
                    ))
                }
            })
        } catch (err) {
            console.error('Chat error:', err)
            setMessages(prev => prev.map(msg =>
                msg.id === placeholderId
                    ? { ...msg, content: 'Sorry, an error occurred. Please try again.', isStreaming: false }
                    : msg
            ))
        } finally {
            setSending(false)
        }
    }

    async function handleSummarize() {
        if (summarizing || summary) return

        setSummarizing(true)
        try {
            const data = await summarizeDocument(documentId)
            setSummary(data.summary)
        } catch (err) {
            console.error('Failed to summarize:', err)
        } finally {
            setSummarizing(false)
        }
    }

    function handleTimestampClick(seconds) {
        if (playerRef.current) {
            playerRef.current.seekTo(seconds)
        }
    }

    function formatTimestamp(seconds) {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    if (loading) {
        return (
            <div className="chat-loading">
                <Loader size={40} className="animate-spin" />
                <p>Loading document...</p>
            </div>
        )
    }

    if (!document) {
        return (
            <div className="chat-error">
                <h2>Document not found</h2>
                <Link to="/dashboard" className="btn btn-primary">
                    Back to Dashboard
                </Link>
            </div>
        )
    }

    const isMediaDocument = document.document_type === 'audio' || document.document_type === 'video'

    return (
        <div className="chat-page">
            {/* Sidebar */}
            <div className="chat-sidebar glass">
                <Link to="/dashboard" className="back-link">
                    <ArrowLeft size={18} />
                    Back to Documents
                </Link>

                <div className="document-details">
                    <h3>{document.original_filename}</h3>
                    <span className="document-type">{document.document_type}</span>
                </div>

                {/* Media Player */}
                {isMediaDocument && (
                    <MediaPlayer
                        ref={playerRef}
                        src={getDocumentFileUrl(documentId)}
                        type={document.document_type}
                        onTimeUpdate={setCurrentTime}
                    />
                )}

                {/* Summary Section */}
                <div className="summary-section">
                    <div className="summary-header">
                        <h4><Sparkles size={16} /> Summary</h4>
                        {!summary && (
                            <button
                                onClick={handleSummarize}
                                className="btn btn-ghost btn-sm"
                                disabled={summarizing}
                            >
                                {summarizing ? <Loader size={14} className="animate-spin" /> : 'Generate'}
                            </button>
                        )}
                    </div>

                    {summary ? (
                        <p className="summary-text">{summary}</p>
                    ) : (
                        <p className="summary-placeholder">
                            Click generate to create an AI summary
                        </p>
                    )}
                </div>

                {/* Timestamps */}
                {isMediaDocument && document.timestamps?.length > 0 && (
                    <div className="timestamps-section">
                        <h4><Clock size={16} /> Timestamps</h4>
                        <div className="timestamps-list">
                            {document.timestamps.map((ts, idx) => (
                                <button
                                    key={idx}
                                    className="timestamp-item"
                                    onClick={() => handleTimestampClick(ts.start)}
                                >
                                    <Play size={14} />
                                    <span className="timestamp-time">{formatTimestamp(ts.start)}</span>
                                    <span className="timestamp-text">{ts.text.slice(0, 50)}...</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Chat Area */}
            <div className="chat-main">
                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="chat-welcome">
                            <Bot size={48} />
                            <h3>Start a conversation</h3>
                            <p>Ask questions about your document</p>

                            <div className="suggested-questions">
                                <button onClick={() => setInput('What is this document about?')}>
                                    What is this document about?
                                </button>
                                <button onClick={() => setInput('Summarize the main points')}>
                                    Summarize the main points
                                </button>
                                <button onClick={() => setInput('What are the key takeaways?')}>
                                    What are the key takeaways?
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`message ${msg.role}`}>
                                    <div className="message-avatar">
                                        {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                                    </div>
                                    <div className="message-content">
                                        {msg.role === 'assistant' ? (
                                            <>
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                {msg.isStreaming && <span className="cursor-blink" />}

                                                {/* Timestamp buttons */}
                                                {msg.timestamps?.length > 0 && (
                                                    <div className="message-timestamps">
                                                        <span className="timestamps-label">
                                                            <Clock size={12} /> Related timestamps:
                                                        </span>
                                                        {msg.timestamps.map((ts, i) => (
                                                            <button
                                                                key={i}
                                                                onClick={() => handleTimestampClick(ts.start)}
                                                                className="timestamp-button"
                                                            >
                                                                <Play size={12} />
                                                                {formatTimestamp(ts.start)}
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            <p>{msg.content}</p>
                                        )}
                                    </div>
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>

                {/* Input */}
                <form onSubmit={handleSubmit} className="chat-input-form">
                    <input
                        type="text"
                        className="input chat-input"
                        placeholder="Ask a question about your document..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={sending}
                    />
                    <button
                        type="submit"
                        className="btn btn-primary btn-icon"
                        disabled={!input.trim() || sending}
                    >
                        {sending ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
                    </button>
                </form>
            </div>
        </div>
    )
}
