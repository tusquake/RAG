import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
    LayoutDashboard, FileText, LogOut, User, Sparkles,
    Menu, X
} from 'lucide-react'
import { useState } from 'react'
import './Layout.css'

export default function Layout({ children }) {
    const { user, logout } = useAuth()
    const location = useLocation()
    const [sidebarOpen, setSidebarOpen] = useState(false)

    const navItems = [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' }
    ]

    return (
        <div className="app-layout">
            {/* Mobile Header */}
            <header className="mobile-header">
                <button
                    className="btn btn-ghost btn-icon"
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                >
                    {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
                <div className="mobile-logo">
                    <Sparkles size={20} />
                    <span>DocuChat</span>
                </div>
            </header>

            {/* Sidebar */}
            <aside className={`app-sidebar ${sidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <Link to="/" className="sidebar-logo">
                        <Sparkles size={24} />
                        <span>DocuChat AI</span>
                    </Link>
                </div>

                <nav className="sidebar-nav">
                    {navItems.map(item => (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
                            onClick={() => setSidebarOpen(false)}
                        >
                            <item.icon size={20} />
                            <span>{item.label}</span>
                        </Link>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    <div className="user-info">
                        <div className="user-avatar">
                            <User size={18} />
                        </div>
                        <div className="user-details">
                            <span className="user-name">{user?.name}</span>
                            <span className="user-email">{user?.email}</span>
                        </div>
                    </div>

                    <button onClick={logout} className="btn btn-ghost logout-btn">
                        <LogOut size={18} />
                        <span>Logout</span>
                    </button>
                </div>
            </aside>

            {/* Overlay for mobile */}
            {sidebarOpen && (
                <div
                    className="sidebar-overlay"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Main Content */}
            <main className="app-main">
                {children}
            </main>
        </div>
    )
}
