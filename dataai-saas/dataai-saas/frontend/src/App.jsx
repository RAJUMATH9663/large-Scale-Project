import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from './store/authStore'

import { LoginPage, RegisterPage } from './pages/Auth'
import DashboardPage from './pages/Dashboard'
import DatasetsPage from './pages/Datasets'
import ChatPage from './pages/Chat'
import {
  PredictionsPage,
  SimulationPage,
  AnomalyPage,
  HistoryPage,
  ExportPage,
  EvaluationPage,
  MonitoringPage,
  AdminPage,
  GraphPage,
} from './pages/OtherPages'

function RequireAuth({ children }) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

function RequireGuest({ children }) {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  const { initAuth } = useAuthStore()

  useEffect(() => {
    initAuth()
  }, [initAuth])

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<RequireGuest><LoginPage /></RequireGuest>} />
      <Route path="/register" element={<RequireGuest><RegisterPage /></RequireGuest>} />

      {/* Protected */}
      <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
      <Route path="/datasets" element={<RequireAuth><DatasetsPage /></RequireAuth>} />
      <Route path="/chat" element={<RequireAuth><ChatPage /></RequireAuth>} />
      <Route path="/predictions" element={<RequireAuth><PredictionsPage /></RequireAuth>} />
      <Route path="/simulation" element={<RequireAuth><SimulationPage /></RequireAuth>} />
      <Route path="/anomaly" element={<RequireAuth><AnomalyPage /></RequireAuth>} />
      <Route path="/graph" element={<RequireAuth><GraphPage /></RequireAuth>} />
      <Route path="/history" element={<RequireAuth><HistoryPage /></RequireAuth>} />
      <Route path="/export" element={<RequireAuth><ExportPage /></RequireAuth>} />
      <Route path="/evaluation" element={<RequireAuth><EvaluationPage /></RequireAuth>} />
      <Route path="/monitoring" element={<RequireAuth><MonitoringPage /></RequireAuth>} />
      <Route path="/admin" element={<RequireAuth><AdminPage /></RequireAuth>} />

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
