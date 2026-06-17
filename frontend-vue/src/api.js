import { store } from './store'

let toastTimer = null

export function showToast(msg, type = 'success', duration = 3000) {
  if (toastTimer) clearTimeout(toastTimer)
  store.toast = { show: true, msg, type }
  toastTimer = setTimeout(() => { store.toast.show = false }, duration)
}

export async function api(method, path, body) {
  const opts = { method, headers: {} }
  if (body instanceof FormData) opts.body = body
  else if (body != null) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body) }
  let r
  try { r = await fetch('/api' + path, opts) } catch (e) { throw new Error('网络错误：无法连接到服务器') }
  if (!r.ok) {
    let msg
    try { const j = await r.json(); msg = j.detail || JSON.stringify(j).slice(0, 200) } catch { msg = r.statusText }
    throw new Error(msg)
  }
  const text = await r.text()
  return text ? JSON.parse(text) : null
}

export function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export { store }