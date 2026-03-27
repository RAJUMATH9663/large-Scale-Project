import { Loader2 } from 'lucide-react'
import clsx from 'clsx'

// ─── Button ───────────────────────────────────────────────────────────────────
export function Button({ children, variant = 'primary', size = 'md', loading, className, ...props }) {
  const base = 'inline-flex items-center gap-2 font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-brand-500 hover:bg-brand-600 text-white shadow-lg shadow-brand-500/20',
    secondary: 'bg-zinc-800 hover:bg-zinc-700 text-zinc-100 border border-zinc-700',
    ghost: 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  }
  const sizes = { sm: 'px-3 py-1.5 text-sm', md: 'px-4 py-2 text-sm', lg: 'px-6 py-3 text-base' }

  return (
    <button className={clsx(base, variants[variant], sizes[size], className)} disabled={loading} {...props}>
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  )
}

// ─── Input ────────────────────────────────────────────────────────────────────
export function Input({ label, error, className, ...props }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-medium text-zinc-300">{label}</label>}
      <input
        className={clsx(
          'bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100',
          'placeholder-zinc-500 focus:outline-none focus:border-brand-500 transition-colors',
          error && 'border-red-500',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}

// ─── Select ───────────────────────────────────────────────────────────────────
export function Select({ label, options = [], className, ...props }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-medium text-zinc-300">{label}</label>}
      <select
        className={clsx(
          'bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100',
          'focus:outline-none focus:border-brand-500 transition-colors',
          className
        )}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

// ─── Card ─────────────────────────────────────────────────────────────────────
export function Card({ children, className, ...props }) {
  return (
    <div className={clsx('bg-zinc-900 border border-zinc-800 rounded-xl p-4', className)} {...props}>
      {children}
    </div>
  )
}

// ─── Badge ────────────────────────────────────────────────────────────────────
export function Badge({ children, variant = 'default' }) {
  const variants = {
    default: 'bg-zinc-800 text-zinc-300',
    success: 'bg-emerald-900/50 text-emerald-400 border border-emerald-800',
    warning: 'bg-amber-900/50 text-amber-400 border border-amber-800',
    error: 'bg-red-900/50 text-red-400 border border-red-800',
    brand: 'bg-brand-900/50 text-brand-400 border border-brand-800',
  }
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium', variants[variant])}>
      {children}
    </span>
  )
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
export function KpiCard({ label, value, sub, icon: Icon, color = '#6366f1' }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-start gap-3">
      {Icon && (
        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: `${color}22`, border: `1px solid ${color}44` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      )}
      <div className="min-w-0">
        <p className="text-xs text-zinc-500 mb-0.5">{label}</p>
        <p className="text-xl font-bold text-zinc-100 font-display truncate">{value}</p>
        {sub && <p className="text-xs text-zinc-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

// ─── Loading Spinner ──────────────────────────────────────────────────────────
export function Spinner({ className }) {
  return <Loader2 className={clsx('animate-spin text-brand-400', className || 'w-6 h-6')} />
}

// ─── Empty State ──────────────────────────────────────────────────────────────
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-4">
        <Icon className="w-7 h-7 text-zinc-600" />
      </div>}
      <p className="text-zinc-300 font-medium mb-1">{title}</p>
      {description && <p className="text-sm text-zinc-500 mb-4 max-w-xs">{description}</p>}
      {action}
    </div>
  )
}

// ─── Section Header ───────────────────────────────────────────────────────────
export function SectionHeader({ title, description, action }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h2 className="text-lg font-semibold font-display text-zinc-100">{title}</h2>
        {description && <p className="text-sm text-zinc-500 mt-0.5">{description}</p>}
      </div>
      {action}
    </div>
  )
}

// ─── Stat Row ─────────────────────────────────────────────────────────────────
export function StatRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
      <span className="text-sm text-zinc-500">{label}</span>
      <span className="text-sm font-medium text-zinc-200 font-mono">{value}</span>
    </div>
  )
}
