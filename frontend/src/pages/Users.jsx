import React, { useState, useEffect } from 'react'
import { Plus, Trash2, UserCheck, UserX } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', full_name: '', role: 'admin' })
  const { user: currentUser } = useAuth()

  useEffect(() => {
    loadUsers()
  }, [])

  async function loadUsers() {
    try {
      const data = await api('/users/')
      setUsers(data.users || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    await api('/users/', {
      method: 'POST',
      body: JSON.stringify(form),
    })
    setShowModal(false)
    setForm({ username: '', password: '', full_name: '', role: 'admin' })
    loadUsers()
  }

  async function handleDelete(id) {
    if (!confirm('Hapus user ini?')) return
    await api(`/users/${id}`, { method: 'DELETE' })
    loadUsers()
  }

  async function handleToggleActive(id) {
    await api(`/users/${id}/toggle-active`, { method: 'POST' })
    loadUsers()
  }

  if (currentUser?.role !== 'superadmin') {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">Hanya superadmin yang dapat mengelola akun</p>
      </div>
    )
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
        <h1 className="text-2xl font-bold text-gray-800">Kelola Akun</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary text-sm flex items-center gap-1">
          <Plus className="w-4 h-4" /> Tambah Admin
        </button>
      </div>

      <div className="card overflow-hidden !p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Username</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Nama</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Role</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Terakhir Login</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-800">{u.username}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.full_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      u.role === 'superadmin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`flex items-center gap-1 text-xs ${
                      u.is_active ? 'text-green-600' : 'text-red-500'
                    }`}>
                      {u.is_active ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                      {u.is_active ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {u.last_login ? new Date(u.last_login).toLocaleString('id-ID') : 'Belum pernah'}
                  </td>
                  <td className="px-4 py-3 flex gap-1">
                    {u.id !== currentUser?.id && (
                      <>
                        <button
                          onClick={() => handleToggleActive(u.id)}
                          className={`p-1.5 rounded-lg text-xs ${
                            u.is_active ? 'text-yellow-600 hover:bg-yellow-50' : 'text-green-600 hover:bg-green-50'
                          }`}
                          title={u.is_active ? 'Nonaktifkan' : 'Aktifkan'}
                        >
                          {u.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => handleDelete(u.id)}
                          className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"
                          title="Hapus"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">Tambah Admin</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-2xl">
                &times;
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
                <input
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                  className="input-field"
                  placeholder="username"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                  className="input-field"
                  placeholder="min 6 karakter"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nama Lengkap *</label>
                <input
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                  className="input-field"
                  placeholder="Nama Admin"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="input-field"
                >
                  <option value="admin">Admin</option>
                  <option value="superadmin">Superadmin</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">Tambah</button>
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">Batal</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
