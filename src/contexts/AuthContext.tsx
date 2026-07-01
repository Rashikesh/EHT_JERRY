"use client"

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import {api} from "@/lib/api";
import Cookies from "js-cookie";

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (
    username: string,
    email: string,
    password: string,
    fullName: string,
    role?: string,
  ) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Load token from localStorage on mount
    const storedToken = localStorage.getItem("access_token")
    if (storedToken) {
      setToken(storedToken)
      // Fetch user info
      api
        .get("/auth/me")
        .then((res : any) => {
          setUser(res.data)
        })
        .catch(() => {
          // Invalid token, clear it
          localStorage.removeItem("access_token")
          Cookies.remove("refresh_token")
          setToken(null)
        })
        .finally(() => {
          setIsLoading(false)
        })
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const formData = new FormData()
    formData.append("username", username)
    formData.append("password", password)

    const res = await api.post("/auth/login", formData)
    const { access_token, refresh_token } = res.data

    localStorage.setItem("access_token", access_token)
    Cookies.set("refresh_token", refresh_token, {
      secure: true,
      sameSite: "strict",
      expires: 7,
    })
    setToken(access_token)

    // Fetch user info
    const userRes = await api.get("/auth/me")
    setUser(userRes.data)
  }

  const register = async (
    username: string,
    email: string,
    password: string,
    fullName: string,
    role: string = "operator",
  ) => {
    await api.post("/auth/register", {
      username,
      email,
      password,
      full_name: fullName,
      role,
    })

    // Auto-login after registration
    await login(username, password)
  }

  const logout = () => {
    api.post("/auth/logout").catch(() => {})
    localStorage.removeItem("access_token")
    Cookies.remove("refresh_token")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}

export default AuthContext;