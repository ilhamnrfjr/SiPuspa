import React, { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { MessageSquare, Users, Clock, Target } from 'lucide-react'
import { api } from '../api/client'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [intents, setIntents] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [summary, hourlyData, confidenceData, intentsData] = await Promise.all([
        api('/analytics/summary'),
        api('/analytics/hourly'),
        api('/analytics/confidence'),
        api('/intents/'),
      ])
      setData({ summary, hourly: hourlyData.hourly, confidence: confidenceData.confidence_stats })
      setIntents(intentsData.intents || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent" />
      </div>
    )
  }

  if (!data) {
    return <p className="text-center text-gray-500">Gagal memuat data</p>
  }

  const stats = [
    { icon: MessageSquare, label: 'Total Percakapan', value: data.summary.total_conversations, color: 'bg-purple-100 text-purple-600' },
    { icon: Users, label: 'Total Pesan', value: data.summary.total_messages, color: 'bg-blue-100 text-blue-600' },
    { icon: Clock, label: 'Avg Response', value: `${data.summary.avg_response_time}s`, color: 'bg-green-100 text-green-600' },
    { icon: Target, label: 'Avg Confidence', value: `${Math.round((data.summary.avg_confidence || 0) * 100)}%`, color: 'bg-pink-100 text-pink-600' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <button onClick={loadData} className="btn-primary text-sm">
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="card">
            <div className={`w-10 h-10 rounded-lg ${s.color} flex items-center justify-center mb-3`}>
              <s.icon className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-gray-800">{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Messages per day */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">Pesan Per Hari (7 hari)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.summary.messages_per_day || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#667eea" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Intents */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">Top Intent</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={(data.summary.top_intents || []).slice(0, 10)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="intent" type="category" tick={{ fontSize: 11 }} width={120} />
              <Tooltip />
              <Bar dataKey="count" fill="#667eea" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Hourly activity */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">Aktivitas Per Jam</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.hourly || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} tickFormatter={(h) => `${String(h).padStart(2, '0')}:00`} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#667eea" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Coverage */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">Intent Coverage</h3>
          {intents.length === 0 ? (
            <p className="text-gray-400 text-sm">Belum ada data</p>
          ) : (
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {intents.map((intent) => {
                const used = (data.summary.top_intents || []).find((t) => t.intent === intent.intent_name)
                return (
                  <div key={intent.intent_name} className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{intent.intent_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">{intent.patterns?.length || 0} patterns</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        used ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                      }`}>
                        {used ? 'Aktif' : 'Belum dipanggil'}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
