import React, { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { api } from '../api/client'

const COLORS = ['#667eea', '#48bb78', '#ed8936', '#fc8181', '#9f7aea', '#f6ad55', '#68d391', '#63b3ed']

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [summary, hourlyData, confidenceData] = await Promise.all([
        api('/analytics/summary'),
        api('/analytics/hourly'),
        api('/analytics/confidence'),
      ])
      setData({
        summary,
        hourly: hourlyData.hourly,
        confidence: confidenceData.confidence_stats,
      })
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

  if (!data) return <p className="text-center text-gray-500">Gagal memuat data</p>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Analytics</h1>
        <button onClick={loadData} className="btn-primary text-sm">Refresh</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tren Harian */}
        <div className="card lg:col-span-2">
          <h3 className="font-semibold text-gray-800 mb-4">📈 Tren Pesan Harian</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data.summary.messages_per_day || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#667eea" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Distribusi Intent */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">🎯 Distribusi Intent</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={(data.summary.top_intents || []).slice(0, 10)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="intent" type="category" tick={{ fontSize: 11 }} width={130} />
              <Tooltip />
              <Bar dataKey="count" fill="#667eea" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Aktivitas Per Jam */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">🕐 Aktivitas Per Jam</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.hourly || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} tickFormatter={(h) => `${String(h).padStart(2, '0')}:00`} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#667eea" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence per Intent */}
        <div className="card lg:col-span-2">
          <h3 className="font-semibold text-gray-800 mb-4">📊 Rata-rata Confidence per Intent</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={(data.confidence || []).map((d) => ({ ...d, pct: Math.round(d.avg_confidence * 100) }))} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
              <YAxis dataKey="intent" type="category" tick={{ fontSize: 11 }} width={130} />
              <Tooltip formatter={(val) => `${val}%`} />
              <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                {(data.confidence || []).map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.avg_confidence >= 0.8 ? '#48bb78' : entry.avg_confidence >= 0.6 ? '#ed8936' : '#fc8181'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500 inline-block" /> &ge;80% (baik)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-orange-400 inline-block" /> 60-80% (cukup)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-400 inline-block" /> &lt;60% (perlu perbaikan)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
