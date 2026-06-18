import { type FormEvent, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { t } from '../lib/i18n'

function LoginBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div className="login-screen__mesh absolute inset-0" />
      <div className="login-screen__grid absolute inset-0" />
      <div className="login-screen__lines absolute inset-0" />
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.07]"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
      >
        <path
          d="M-40 720 C 180 580, 320 640, 520 480 S 920 360, 1180 280 S 1420 200, 1520 120"
          stroke="url(#login-gold)"
          strokeWidth="1.5"
        />
        <path
          d="M-40 780 C 220 680, 400 720, 620 560 S 980 440, 1240 380 S 1460 320, 1540 240"
          stroke="url(#login-brand)"
          strokeWidth="1"
          opacity="0.7"
        />
        <defs>
          <linearGradient id="login-gold" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#c9a227" stopOpacity="0" />
            <stop offset="35%" stopColor="#e8c547" />
            <stop offset="100%" stopColor="#c9a227" stopOpacity="0.2" />
          </linearGradient>
          <linearGradient id="login-brand" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#991b1b" stopOpacity="0" />
            <stop offset="50%" stopColor="#b91c1c" />
            <stop offset="100%" stopColor="#dc2626" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-gold-400/10 blur-3xl" />
      <div className="absolute -bottom-32 -left-20 h-80 w-80 rounded-full bg-brand-500/8 blur-3xl" />
    </div>
  )
}

export function LoginPage() {
  const { user, login, prefs } = useAuth()
  const lang = prefs.lang
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  if (user) return <Navigate to="/" replace />

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setMsg('')
    try {
      if (mode === 'login') {
        await login(username, password)
      } else {
        if (password !== confirm) {
          setError(t('auth.pwd_mismatch', lang))
          return
        }
        await api.register(username, password)
        setMsg(t('auth.register_ok', lang))
        setMode('login')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error')
    }
  }

  return (
    <div className="login-screen relative min-h-screen flex items-center justify-center p-4 overflow-hidden">
      <LoginBackground />
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-xs font-semibold tracking-[0.2em] text-stone-400 uppercase">IAMS</div>
          <h1 className="text-3xl font-extrabold text-brand-700 mt-2 drop-shadow-sm">{t('app.title', lang)}</h1>
          <div className="w-9 h-1 mx-auto mt-3 rounded-full bg-gradient-to-r from-gold-500 to-brand-500 shadow-sm shadow-gold-500/30" />
          <p className="mt-4 text-sm text-stone-500 tracking-wide">{t('auth.tagline', lang)}</p>
        </div>
        <div className="login-card overflow-hidden">
          <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-brand-500" />
          <div className="p-6">
            <div className="flex rounded-xl bg-stone-100/80 p-1 mb-6">
              {(['login', 'register'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  className={`flex-1 rounded-lg py-2.5 text-sm font-medium transition ${
                    mode === m ? 'bg-white shadow-sm text-brand-700' : 'text-stone-500 hover:text-stone-600'
                  }`}
                  onClick={() => setMode(m)}
                >
                  {m === 'login' ? t('auth.login', lang) : t('auth.register', lang)}
                </button>
              ))}
            </div>
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="text-sm text-stone-600">{t('auth.username', lang)}</label>
                <input className="input mt-1 bg-white/90" value={username} onChange={(e) => setUsername(e.target.value)} required />
              </div>
              <div>
                <label className="text-sm text-stone-600">{t('auth.password', lang)}</label>
                <input
                  className="input mt-1 bg-white/90"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {mode === 'register' && (
                <div>
                  <label className="text-sm text-stone-600">{t('auth.confirm', lang)}</label>
                  <input
                    className="input mt-1 bg-white/90"
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                  />
                </div>
              )}
              {error && <p className="text-sm text-red-600">{error}</p>}
              {msg && <p className="text-sm text-green-600">{msg}</p>}
              <button type="submit" className="btn-primary w-full shadow-md shadow-brand-600/15">
                {mode === 'login' ? t('auth.login', lang) : t('auth.register', lang)}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
