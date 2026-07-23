import React, { useState, useEffect } from 'react'
import { Plus, Edit3, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import { api } from '../api/client'

export default function Intents() {
  const [intents, setIntents] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState(null)
  const [expanded, setExpanded] = useState({})
  const [form, setForm] = useState({
    intent_name: '',
    patterns: '',
    response_text: '',
    quick_replies: '',
  })

  useEffect(() => {
    loadIntents()
  }, [])

  async function loadIntents() {
    try {
      const data = await api('/intents/')
      setIntents(data.intents || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function openAdd() {
    setEditing(null)
    setForm({ intent_name: '', patterns: '', response_text: '', quick_replies: '' })
    setShowModal(true)
  }

  function openEdit(intent) {
    setEditing(intent.intent_name)
    setForm({
      intent_name: intent.intent_name,
      patterns: (intent.patterns || []).join('\n'),
      response_text: intent.response_text || '',
      quick_replies: (intent.quick_replies || []).join(', '),
    })
    setShowModal(true)
  }

  async function handleSave(e) {
    e.preventDefault()
    const payload = {
      intent_name: form.intent_name.trim(),
      patterns: form.patterns.split('\n').map((p) => p.trim()).filter(Boolean),
      response_text: form.response_text.trim(),
      quick_replies: form.quick_replies.split(',').map((q) => q.trim()).filter(Boolean),
    }

    if (editing) {
      await api(`/intents/${editing}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
    } else {
      await api('/intents/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    }

    setShowModal(false)
    loadIntents()
  }

  async function handleDelete(name) {
    if (!confirm(`Hapus intent "${name}"?`)) return
    await api(`/intents/${name}`, { method: 'DELETE' })
    loadIntents()
  }

  function toggleExpand(name) {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Kelola Intent</h1>
        <button onClick={openAdd} className="btn-primary text-sm flex items-center gap-1">
          <Plus className="w-4 h-4" /> Tambah Intent
        </button>
      </div>

      <div className="space-y-3">
        {intents.length === 0 ? (
          <div className="card text-center text-gray-400">Belum ada intent</div>
        ) : (
          intents.map((intent) => (
            <div key={intent.intent_name} className="card !p-0 overflow-hidden">
              <button
                onClick={() => toggleExpand(intent.intent_name)}
                className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-all"
              >
                <div className="flex items-center gap-3">
                  {expanded[intent.intent_name] ? (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  )}
                  <span className="font-medium text-gray-800">{intent.intent_name}</span>
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                    {intent.patterns?.length || 0} patterns
                  </span>
                </div>
                <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => openEdit(intent)} className="p-1.5 text-blue-500 hover:bg-blue-50 rounded-lg">
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button onClick={() => handleDelete(intent.intent_name)} className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </button>

              {expanded[intent.intent_name] && (
                <div className="px-6 pb-4 space-y-3 border-t border-gray-100 pt-3">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">PATTERNS</p>
                    <div className="flex flex-wrap gap-1">
                      {(intent.patterns || []).map((p, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">RESPONSE</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-3">
                      {intent.response_text}
                    </p>
                  </div>
                  {intent.quick_replies?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">QUICK REPLIES</p>
                      <div className="flex flex-wrap gap-1">
                        {(intent.quick_replies || []).map((qr, i) => (
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
          ))
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">
                {editing ? 'Edit Intent' : 'Tambah Intent'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-2xl">
                &times;
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nama Intent *</label>
                <input
                  value={form.intent_name}
                  onChange={(e) => setForm({ ...form, intent_name: e.target.value })}
                  required
                  className="input-field"
                  placeholder="contoh: jam_operasional"
                  disabled={!!editing}
                />
                <p className="text-xs text-gray-400 mt-1">Nama unik tanpa spasi, gunakan underscore</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patterns *</label>
                <textarea
                  value={form.patterns}
                  onChange={(e) => setForm({ ...form, patterns: e.target.value })}
                  rows={5}
                  required
                  className="input-field"
                  placeholder="jam buka perpustakaan&#10;perpustakaan buka jam berapa"
                />
                <p className="text-xs text-gray-400 mt-1">Satu pattern per baris</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Response Text *</label>
                <textarea
                  value={form.response_text}
                  onChange={(e) => setForm({ ...form, response_text: e.target.value })}
                  rows={6}
                  required
                  className="input-field text-sm"
                  placeholder="**Jam Operasional Perpustakaan**&#10;• Senin–Jumat: 08.00–16.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quick Replies (koma)</label>
                <input
                  value={form.quick_replies}
                  onChange={(e) => setForm({ ...form, quick_replies: e.target.value })}
                  className="input-field"
                  placeholder="Lokasi, Cara Pinjam, Fasilitas"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">
                  Simpan
                </button>
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                  Batal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
