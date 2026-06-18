import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, type UserPrefs } from '../lib/api'
import { normalizePrefs, pnlColorsForLang } from '../lib/prefsNormalize'

interface AuthState {
  user: string | null
  loading: boolean
  prefs: UserPrefs
  setPrefs: (p: Partial<UserPrefs>) => void
  refreshPrefs: () => Promise<void>
  login: (u: string, p: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const defaultPrefs: UserPrefs = normalizePrefs({})

const AuthContext = createContext<AuthState | null>(null)

function mergePrefs(raw: Partial<UserPrefs>): UserPrefs {
  const merged = normalizePrefs({ ...defaultPrefs, ...raw })
  return { ...merged, pnl_colors: pnlColorsForLang(merged.lang) }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [prefs, setPrefsState] = useState<UserPrefs>(defaultPrefs)

  const refreshPrefs = async () => {
    const p = await api.prefs()
    setPrefsState(mergePrefs(p))
  }

  const refresh = async () => {
    try {
      const me = await api.me()
      setUser(me.username)
      await refreshPrefs()
    } catch {
      setUser(null)
      try {
        const p = await api.prefs()
        setPrefsState(mergePrefs(p))
      } catch {
        setPrefsState(defaultPrefs)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const login = async (username: string, password: string) => {
    await api.login(username, password)
    setUser(username)
    await refreshPrefs()
  }

  const logout = async () => {
    await api.logout()
    setUser(null)
  }

  const setPrefs = (partial: Partial<UserPrefs>) => {
    setPrefsState((prev) => mergePrefs({ ...prev, ...partial }))
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, prefs, setPrefs, refreshPrefs, login, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside provider')
  return ctx
}
