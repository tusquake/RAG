import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Upload, MessageSquare, FileText, Music, Video, Sparkles, ArrowRight } from 'lucide-react'
import './Home.css'

export default function Home() {
    const { isAuthenticated } = useAuth()

    const features = [
        {
            icon: <FileText size={32} />,
            title: 'PDF Documents',
            description: 'Upload and analyze PDF documents with AI-powered Q&A'
        },
        {
            icon: <Music size={32} />,
            title: 'Audio Files',
            description: 'Transcribe audio with timestamps and ask questions'
        },
        {
            icon: <Video size={32} />,
            title: 'Video Files',
            description: 'Extract insights from video content with playback'
        },
        {
            icon: <MessageSquare size={32} />,
            title: 'AI Chat',
            description: 'Intelligent Q&A with context from your documents'
        },
        {
            icon: <Sparkles size={32} />,
            title: 'Summarization',
            description: 'Generate concise summaries of your content'
        },
        {
            icon: <Upload size={32} />,
            title: 'Easy Upload',
            description: 'Drag and drop files for instant processing'
        }
    ]

    return (
        <div className="home">
            {/* Hero Section */}
            <header className="home-header">
                <nav className="home-nav container">
                    <div className="logo">
                        <Sparkles className="logo-icon" />
                        <span>DocuChat AI</span>
                    </div>
                    <div className="nav-links">
                        {isAuthenticated ? (
                            <Link to="/dashboard" className="btn btn-primary">
                                Dashboard <ArrowRight size={16} />
                            </Link>
                        ) : (
                            <>
                                <Link to="/login" className="btn btn-ghost">Login</Link>
                                <Link to="/register" className="btn btn-primary">Get Started</Link>
                            </>
                        )}
                    </div>
                </nav>

                <div className="hero container">
                    <div className="hero-content">
                        <h1 className="hero-title">
                            AI-Powered
                            <span className="gradient-text"> Document Q&A</span>
                        </h1>
                        <p className="hero-description">
                            Upload PDFs, audio, and video files. Ask questions and get intelligent answers
                            with timestamps and source references. Powered by advanced AI.
                        </p>
                        <div className="hero-actions">
                            <Link to={isAuthenticated ? "/dashboard" : "/register"} className="btn btn-primary btn-lg">
                                {isAuthenticated ? "Go to Dashboard" : "Start for Free"}
                                <ArrowRight size={20} />
                            </Link>
                            <a href="#features" className="btn btn-secondary btn-lg">
                                Learn More
                            </a>
                        </div>
                    </div>

                    <div className="hero-visual">
                        <div className="hero-card glass">
                            <div className="chat-preview">
                                <div className="chat-message user">
                                    What is the main topic of this document?
                                </div>
                                <div className="chat-message assistant">
                                    <div className="typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Features Section */}
            <section id="features" className="features container">
                <h2 className="section-title">Powerful Features</h2>
                <p className="section-description">
                    Everything you need to interact with your documents intelligently
                </p>

                <div className="features-grid">
                    {features.map((feature, index) => (
                        <div key={index} className="feature-card card">
                            <div className="feature-icon">{feature.icon}</div>
                            <h3>{feature.title}</h3>
                            <p>{feature.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta container">
                <div className="cta-content glass">
                    <h2>Ready to Get Started?</h2>
                    <p>Upload your first document and experience AI-powered Q&A</p>
                    <Link to={isAuthenticated ? "/dashboard" : "/register"} className="btn btn-primary btn-lg">
                        {isAuthenticated ? "Go to Dashboard" : "Create Free Account"}
                    </Link>
                </div>
            </section>

            {/* Footer */}
            <footer className="home-footer">
                <div className="container">
                    <p>© 2024 DocuChat AI. Built with ❤️ and AI.</p>
                </div>
            </footer>
        </div>
    )
}
