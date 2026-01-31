import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [token, setToken] = useState(() => localStorage.getItem('token'))

    useEffect(() => {
        checkAuth()
    }, [])

    async function checkAuth() {
        const storedToken = localStorage.getItem('token')
        if (storedToken) {
            try {
                const userData = await getCurrentUser(storedToken)
                setUser(userData)
                setToken(storedToken)
            } catch (error) {
                console.error('Auth check failed:', error)
                localStorage.removeItem('token')
                setToken(null)
            }
        }
        setLoading(false)
    }

    async function login(email, password) {
        const response = await apiLogin(email, password)
        localStorage.setItem('token', response.access_token)
        setToken(response.access_token)
        setUser(response.user)
        return response
    }

    async function register(email, password, name) {
        const response = await apiRegister(email, password, name)
        localStorage.setItem('token', response.access_token)
        setToken(response.access_token)
        setUser(response.user)
        return response
    }

    function logout() {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
    }

    const value = {
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
