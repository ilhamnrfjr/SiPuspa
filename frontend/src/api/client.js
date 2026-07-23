const API_BASE = '/api'

function getToken() {
  return localStorage.getItem('admin_token')
}

export async function api(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    localStorage.removeItem('admin_token')
    window.location.href = '/dashboard/login'
    throw new Error('Unauthorized')
  }

  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Request gagal')
  }
  return data
}

export function apiAuth() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}
