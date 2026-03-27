import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Button, Input } from '../components/UI'
import toast from 'react-hot-toast'
import { Zap } from 'lucide-react'

export default function AuthPage({ initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode)
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuthStore()
  const navigate = useNavigate()

  const handle = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(form.email, form.username, form.password)
      }
      toast.success(`Welcome${mode === 'register' ? ' to DataAI!' : ' back!'}`)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-sm px-4 animate-fadein">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mb-4 shadow-2xl shadow-brand-500/30">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold font-display text-zinc-100">DataAI</h1>
          <p className="text-sm text-zinc-500 mt-1">Intelligent Data Analytics Platform</p>
        </div>

        {/* Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
          {/* Tab switch */}
          <div className="flex bg-zinc-950 rounded-lg p-1 mb-6">
            {['login', 'register'].map((m) => (
              <button key={m} onClick={() => setMode(m)}
                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-all capitalize ${
                  mode === m ? 'bg-brand-500 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'
                }`}>
                {m === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <form onSubmit={handle} className="flex flex-col gap-4">
            <Input label="Email" type="email" placeholder="you@example.com"
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />

            {mode === 'register' && (
              <Input label="Username" placeholder="yourname"
                value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            )}

            <Input label="Password" type="password" placeholder="••••••••"
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />

            <Button type="submit" loading={loading} className="w-full justify-center mt-1">
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </Button>
          </form>

          {/* Demo hint */}
          <p className="text-center text-xs text-zinc-600 mt-4">
            Demo: any email + password works for the first registration
          </p>
        </div>
      </div>
    </div>
  )
}

// Named exports for App.jsx router
export function LoginPage() {
  return <AuthPage initialMode="login" />
}
export function RegisterPage() {
  return <AuthPage initialMode="register" />
}
