import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useSearchParams } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AppShell, ClientShell } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { HallPage } from './pages/HallPage'
import { legacyClientPath } from './lib/legacyClientUrl'
import { t } from './lib/i18n'
import { SettingsPage } from './pages/SettingsPage'

const AnalyticsPage = lazy(() =>
  import('./pages/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage })),
)
const ClientPage = lazy(() =>
  import('./pages/ClientPage').then((m) => ({ default: m.ClientPage })),
)

const qc = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading, prefs } = useAuth()
  const location = useLocation()
  const [params] = useSearchParams()
  const legacyTarget = legacyClientPath(params)

  if (legacyTarget && location.pathname === '/') {
    return <Navigate to={legacyTarget} replace />
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-stone-500">
        {t('common.loading', prefs.lang)}
      </div>
    )
  }
  if (!user) return <Navigate to={`/login${location.search}`} replace />
  return <>{children}</>
}

function HallEntry() {
  return <HallPage />
}

function LoginEntry() {
  const [params] = useSearchParams()
  const target = legacyClientPath(params)
  if (target) return <Navigate to={target} replace />
  return <LoginPage />
}

function PageLoading() {
  const { prefs } = useAuth()
  return (
    <div className="min-h-[40vh] flex items-center justify-center text-stone-500">
      {t('common.loading', prefs.lang)}
    </div>
  )
}

function ClientRoute() {
  const location = useLocation()
  return (
    <ClientShell>
      <ClientPage key={location.key} />
    </ClientShell>
  )
}

function AppRoutes() {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route path="/login" element={<LoginEntry />} />
        <Route path="/client/:username/:accountName" element={<ClientRoute />} />
        <Route
          path="/"
          element={
            <Protected>
              <AppShell />
            </Protected>
          }
        >
          <Route index element={<HallEntry />} />
          <Route path="account/:accountName" element={<AnalyticsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter basename="/IAMS">
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
