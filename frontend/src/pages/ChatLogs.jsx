import React, { useState, useEffect } from 'react'
import { Search, Download, Trash2, X, MessageSquare } from 'lucide-react'
import { api } from '../api/client'

export default function ChatLogs() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [intentFilter, setIntentFilter] = useState('')
  const [intents, setIntents] = useState([])
  const [page, setPage] = useState(0)
  const [selectedSession, setSelectedSession] = useState(null)
  const [sessionDetail, setSessionDetail] = useState(null)
  const limit = 50

  useEffect(() => {
    loadIntents()
  }, [])

  useEffect(() => {
    loadLogs()
  }, [search, intentFilter, page])

  async function loadIntents() {
    try {
      const data = await api('/intents/')
      setIntents(data.intents || [])
    } catch (err) {
      console.error(err)
    }
  }

  async function loadLogs() {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit, offset: page * limit })
      if (search) params.append('search', search)
      if (intentFilter) params.append('intent', intentFilter)
      const data = await api(`/analytics/logs?${params}`)
      setLogs(data.logs || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function openSession(sessionId) {
    setSelectedSession(sessionId)
    const data = await api(`/analytics/logs?limit=500&search=${sessionId}`)
    const msgs = (data.logs || []).filter((l) => l.session_id === sessionId)
    setSessionDetail(msgs)
  }

  async function deleteLog(id) {
    if (!confirm('Hapus log ini?')) return
    await api(`/analytics/logs/${id}`, { method: 'DELETE' })
    loadLogs()
  }

  async function deleteAllLogs() {
    if (!confirm('⚠️ Hapus SEMUA log?\nPastikan sudah backup!')) return
    await api('/analytics/logs', { method: 'DELETE' })
    loadLogs()
  }

  async function exportCsv() {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/analytics/logs/export`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `backup_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Chat Logs</h1>
        <div className="flex gap-2">
          <button onClick={exportCsv} className="btn-primary text-sm flex items-center gap-1">
            <Download className="w-4 h-4" /> Backup CSV
          </button>
          <button onClick={deleteAllLogs} className="btn-danger text-sm flex items-center gap-1">
            <Trash2 className="w-4 h-4" /> Hapus Semua
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 text-gray-400 w-4 h-4" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0) }}
            placeholder="Cari pesan..."
            className="input-field pl-9"
          />
        </div>
        <select
          value={intentFilter}
          onChange={(e) => { setIntentFilter(e.target.value); setPage(0) }}
          className="input-field w-auto"
        >
          <option value="">Semua Intent</option>
          {intents.map((i) => (
            <option key={i.intent_name} value={i.intent_name}>{i.intent_name}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden !p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-primary-500 to-primary-700 text-white">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold">Waktu</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Pesan</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Intent</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Confidence</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Response</th>
                <th className="px-4 py-3 text-left text-xs font-semibold">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Memuat...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada log</td></tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString('id-ID') : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-800 max-w-xs truncate">{log.user_message}</div>
                      <div className="text-xs text-gray-400 truncate max-w-xs">{log.bot_response}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">
                        {log.intent || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {log.confidence ? `${Math.round(log.confidence * 100)}%` : '-'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{log.response_time?.toFixed(3)}s</td>
                    <td className="px-4 py-3">
                      <button onClick={() => deleteLog(log.id)} className="text-red-500 hover:text-red-700">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => setPage(i)}
              className={`px-3 py-1 rounded text-sm ${page === i ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}

      <p className="text-center text-sm text-gray-400">{total} total log</p>
    </div>
  )
}
