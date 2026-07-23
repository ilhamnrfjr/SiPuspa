import React, { useState } from 'react'
import { FlaskConical, Send, AlertCircle, CheckCircle } from 'lucide-react'
import { api } from '../api/client'

export default function Training() {
  const [testInput, setTestInput] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])

  async function handleTest() {
    if (!testInput.trim()) return
    setLoading(true)
    try {
      const data = await api('/training/test', {
        method: 'POST',
        body: JSON.stringify({ message: testInput.trim() }),
      })
      setResult(data)
      setHistory((prev) => [
        { message: testInput.trim(), result: data, timestamp: new Date().toLocaleTimeString() },
        ...prev,
      ])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleTest()
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Pelatihan NLU</h1>

      {/* Test Panel */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-2">🧪 Uji Pesan</h3>
        <p className="text-sm text-gray-500 mb-4">Ketik pesan untuk melihat intent, confidence, dan response preview</p>

        <div className="flex gap-3">
          <input
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ketik pesan uji..."
            className="input-field flex-1"
          />
          <button
            onClick={handleTest}
            disabled={loading || !testInput.trim()}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Uji
          </button>
        </div>

        {result && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                result.intent !== 'not_understood' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'
              }`}>
                {result.intent !== 'not_understood' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                <span className="font-medium">{result.intent}</span>
              </div>
              <div className="text-sm text-gray-500">
                Confidence: <strong>{Math.round(result.confidence * 100)}%</strong>
              </div>
            </div>

            {result.matched_pattern && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">MATCHED PATTERN</p>
                <p className="text-sm text-gray-700 bg-gray-50 rounded-lg px-3 py-2">{result.matched_pattern}</p>
              </div>
            )}

            {Object.keys(result.entities || {}).length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">ENTITIES</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(result.entities).map(([k, v]) => (
                    <span key={k} className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded text-xs">
                      {k}: {v}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.response_preview && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">RESPONSE PREVIEW</p>
                <div className="text-sm text-gray-700 bg-gray-50 rounded-lg px-4 py-3 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {result.response_preview}
                </div>
              </div>
            )}

            {result.quick_replies?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">QUICK REPLIES</p>
                <div className="flex flex-wrap gap-1">
                  {result.quick_replies.map((qr, i) => (
                    <span key={i} className="px-2 py-0.5 bg-primary-50 text-primary-600 rounded text-xs">
                      {qr}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* History */}
      {history.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4">📋 Riwayat Pengujian</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {history.map((h, i) => (
              <div key={i} className="flex items-center gap-3 text-sm p-2 hover:bg-gray-50 rounded-lg">
                <span className="text-xs text-gray-400 w-16">{h.timestamp}</span>
                <span className="flex-1 text-gray-700 truncate">{h.message}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  h.result.intent !== 'not_understood' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                }`}>
                  {h.result.intent}
                </span>
                <span className="text-xs text-gray-400 w-12 text-right">
                  {Math.round(h.result.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
