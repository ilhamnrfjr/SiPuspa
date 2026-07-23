import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, BarChart3, MessageSquare, Workflow,
  Users, FlaskConical, LogOut, BookOpen,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/dashboard/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/dashboard/logs', icon: MessageSquare, label: 'Chat Logs' },
  { to: '/dashboard/intents', icon: Workflow, label: 'Kelola Intent' },
  { to: '/dashboard/training', icon: FlaskConical, label: 'Pelatihan NLU' },
  { to: '/dashboard/users', icon: Users, label: 'Kelola Akun' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 shadow-sm flex flex-col z-50">
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-gray-800 text-sm">PUSPA</h2>
            <p className="text-xs text-gray-400">Perpustakaan BPK RI</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
            {user?.full_name?.charAt(0) || 'A'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">
              {user?.full_name || 'Admin'}
            </p>
            <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-red-500 hover:text-red-700 w-full px-3 py-2 rounded-lg hover:bg-red-50 transition-all"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>

      <a
        href="/chat"
        target="_blank"
        className="m-3 p-3 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-xl text-sm font-medium text-center hover:shadow-lg transition-all"
      >
        💬 Demo Chat
      </a>
    </aside>
  )
}
