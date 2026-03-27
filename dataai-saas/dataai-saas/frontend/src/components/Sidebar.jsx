import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import clsx from 'clsx'
import {
  LayoutDashboard, Upload, MessageSquare, GitFork, LineChart,
  Sliders, AlertTriangle, Clock, Download, BarChart3, Activity,
  Settings, LogOut, Shield, ChevronRight, Zap, Brain
} from 'lucide-react'

const nav = [
  { group: 'Core', items: [
    { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Datasets', to: '/datasets', icon: Upload },
    { label: 'AI Chat', to: '/chat', icon: MessageSquare },
  ]},
  { group: 'Analytics', items: [
    { label: 'Predictions', to: '/predictions', icon: LineChart },
    { label: 'Simulation', to: '/simulation', icon: Sliders },
    { label: 'Anomalies', to: '/anomaly', icon: AlertTriangle },
    { label: 'Graph Explorer', to: '/graph', icon: GitFork },
  ]},
  { group: 'Intelligence', items: [
    { label: 'Evaluation', to: '/evaluation', icon: Brain },
    { label: 'Monitoring', to: '/monitoring', icon: Activity },
    { label: 'History', to: '/history', icon: Clock },
    { label: 'Export', to: '/export', icon: Download },
  ]},
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-56 h-screen flex-shrink-0 bg-zinc-950 border-r border-zinc-800/60 flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-zinc-800/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold font-display text-zinc-100">DataAI</p>
            <p className="text-[10px] text-zinc-500 leading-none">SaaS Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {nav.map((group) => (
          <div key={group.group} className="mb-5">
            <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest px-2 mb-1.5">
              {group.group}
            </p>
            {group.items.map(({ label, to, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all duration-150 mb-0.5',
                    isActive
                      ? 'bg-brand-500/15 text-brand-400 font-medium'
                      : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60'
                  )
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {label}
              </NavLink>
            ))}
          </div>
        ))}

        {user?.role === 'admin' && (
          <div className="mb-5">
            <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest px-2 mb-1.5">Admin</p>
            <NavLink to="/admin"
              className={({ isActive }) =>
                clsx('flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all mb-0.5',
                  isActive ? 'bg-brand-500/15 text-brand-400 font-medium' : 'text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60')
              }>
              <Shield className="w-4 h-4" /> Admin Panel
            </NavLink>
          </div>
        )}
      </nav>

      {/* User Footer */}
      <div className="px-3 py-3 border-t border-zinc-800/60">
        <div className="flex items-center gap-2 mb-2 px-1">
          <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold text-white">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-zinc-300 truncate">{user?.username}</p>
            <p className="text-[10px] text-zinc-500 truncate">{user?.role}</p>
          </div>
        </div>
        <button onClick={handleLogout}
          className="flex items-center gap-2 w-full px-2.5 py-1.5 text-xs text-zinc-500 hover:text-red-400 hover:bg-zinc-800/60 rounded-lg transition-all">
          <LogOut className="w-3.5 h-3.5" /> Sign out
        </button>
      </div>
    </aside>
  )
}
