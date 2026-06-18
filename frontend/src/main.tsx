import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ErrorBoundary } from './components/ErrorBoundary'
import { bootLang } from './lib/bootLang'
import { t } from './lib/i18n'

const lang = bootLang()
const rootEl = document.getElementById('root')
if (!rootEl) {
  document.body.innerHTML = `<p style="padding:2rem;color:#991b1b">IAMS: root element missing</p>`
} else {
  createRoot(rootEl).render(
    <ErrorBoundary
      title={t('boot.render_fail', lang)}
      fallback={
        <div style={{ padding: '2rem', fontFamily: 'system-ui,sans-serif', color: '#44403c' }}>
          <h1 style={{ color: '#991b1b', fontSize: '1.25rem' }}>{t('boot.fail_title', lang)}</h1>
          <p style={{ marginTop: '0.75rem' }}>
            {t('boot.fail_hint', lang)}{' '}
            <a href="/IAMS/login">/IAMS/login</a>
          </p>
        </div>
      }
    >
      <App />
    </ErrorBoundary>,
  )
}
