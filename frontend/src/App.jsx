import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ChatDemo from './pages/ChatDemo'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import ChatLogs from './pages/ChatLogs'
import Intents from './pages/Intents'
import Users from './pages/Users'
import Training from './pages/Training'
import Layout from './components/Layout'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<ChatDemo />} />
        <Route path="/chat" element={<ChatDemo />} />
        <Route path="/dashboard/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <Layout>
              <Dashboard />
            </Layout>
          }
        />
        <Route
          path="/dashboard/analytics"
          element={
            <Layout>
              <Analytics />
            </Layout>
          }
        />
        <Route
          path="/dashboard/logs"
          element={
            <Layout>
              <ChatLogs />
            </Layout>
          }
        />
        <Route
          path="/dashboard/intents"
          element={
            <Layout>
              <Intents />
            </Layout>
          }
        />
        <Route
          path="/dashboard/users"
          element={
            <Layout>
              <Users />
            </Layout>
          }
        />
        <Route
          path="/dashboard/training"
          element={
            <Layout>
              <Training />
            </Layout>
          }
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </AuthProvider>
  )
}
