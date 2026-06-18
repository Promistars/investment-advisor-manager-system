import { Component, type ErrorInfo, type ReactNode } from 'react'
import { bootLang } from '../lib/bootLang'
import { t } from '../lib/i18n'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  title?: string
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="card p-4 text-sm text-red-700 bg-red-50">
          {this.props.title ? <p className="font-semibold mb-1">{this.props.title}</p> : null}
          <p>{this.state.error.message || t('boot.render_fail', bootLang())}</p>
        </div>
      )
    }
    return this.props.children
  }
}
