/** Vite base, e.g. `/IAMS/` */
export const APP_BASE = import.meta.env.BASE_URL

/** App-relative path under the mount (leading slash optional). */
export function appPath(path: string): string {
  const trimmed = path.replace(/^\/+/, '')
  return `${APP_BASE}${trimmed}`
}

/** Absolute URL for share links and external `<a href>`. */
export function appUrl(path: string): string {
  return `${window.location.origin}${appPath(path)}`
}
