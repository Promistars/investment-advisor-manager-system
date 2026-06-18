import type { ReactNode } from 'react'
import { NavLink, Outlet, useMatch, useSearchParams } from 'react-router-dom'
import { Building2, Settings } from 'lucide-react'
import { AccountSidebar } from './AdminTools'
import { useAuth } from '../context/AuthContext'
import { t, e, type Lang } from '../lib/i18n'

function AccountSidebarRail() {
  const match = useMatch('/account/:accountName')
  if (!match?.params.accountName) return null
  const account = decodeURIComponent(match.params.accountName)
  return <AccountSidebar key={account} account={account} />
}

export function AppShell() {
  const { user, prefs, logout } = useAuth()
  const lang = prefs.lang
  const showEmoji = prefs.show_emoji

  return (
    <div className={`min-h-screen flex ${prefs.compact_ui ? 'text-[13px]' : ''}`}>
      <aside className="no-print sticky top-0 h-screen w-64 shrink-0 self-start border-r border-brand-100 bg-white/95 backdrop-blur flex flex-col overflow-x-hidden overflow-y-auto">
        <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-brand-500" />
        <div className="px-4 pt-5 pb-4 min-w-0">
          <div className="text-xs font-semibold tracking-widest text-stone-400 uppercase">IAMS</div>
          <h1 className="text-base font-bold text-brand-700 mt-1 leading-snug break-words">{t('app.title', lang)}</h1>
        </div>
        <nav className="px-4 space-y-1 min-w-0">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive ? 'bg-brand-50 text-brand-700 border-l-2 border-gold-500' : 'text-stone-600 hover:bg-stone-50'
              }`
            }
          >
            <Building2 size={18} className="shrink-0" /> <span className="truncate">{e('nav.hall', lang, '🏠', showEmoji)}</span>
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive ? 'bg-brand-50 text-brand-700 border-l-2 border-gold-500' : 'text-stone-600 hover:bg-stone-50'
              }`
            }
          >
            <Settings size={18} className="shrink-0" /> <span className="truncate">{e('nav.settings', lang, '⚙️', showEmoji)}</span>
          </NavLink>
        </nav>
        <div className="flex-1 min-h-0 min-w-0 overflow-y-auto overflow-x-hidden">
          <AccountSidebarRail />
        </div>
        <div className="px-4 py-4 border-t border-brand-100 shrink-0 min-w-0">
          <div className="text-xs text-stone-500 mb-2 truncate" title={user ?? ''}>{user}</div>
          <button type="button" className="btn-secondary w-full text-xs whitespace-normal leading-snug" onClick={() => logout()}>
            {e('auth.logout', lang, '🚪', showEmoji)}
          </button>
        </div>
      </aside>
      <main className="flex-1 min-w-0 p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  )
}

export function ClientShell({ children }: { children?: ReactNode }) {
  const [params] = useSearchParams()
  const lang: Lang = params.get('lang') === 'en' ? 'en' : 'zh'
  return (
    <div className="min-h-screen">
      <div className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-brand-100 shadow-sm">
        <div className="h-1 bg-gradient-to-r from-gold-500 via-gold-400 to-brand-500" />
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-stone-400 tracking-wide">{t('layout.client_badge', lang)}</div>
          </div>
          <button type="button" className="btn-secondary no-print" onClick={() => window.print()}>
            {t('layout.print', lang)}
          </button>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-4 py-6">{children ?? <Outlet />}</div>
    </div>
  )
}
