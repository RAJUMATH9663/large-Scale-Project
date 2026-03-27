// ─── Predictions Page ─────────────────────────────────────────────────────────
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { datasetsApi, predictionApi } from '../services/api'
import { Button, Card, Select, Spinner, KpiCard, EmptyState, SectionHeader } from '../components/UI'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts'
import { TrendingUp, Play } from 'lucide-react'

export function PredictionsPage() {
  const [datasetId, setDatasetId] = useState('')
  const [targetCol, setTargetCol] = useState('')
  const [modelType, setModelType] = useState('random_forest')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => datasetsApi.list().then(r => r.data) })
  const { data: dsInfo } = useQuery({
    queryKey: ['dsinfo', datasetId], enabled: !!datasetId,
    queryFn: () => datasetsApi.stats(datasetId).then(r => r.data),
  })

  const numCols = dsInfo?.columns?.filter(c => ['int64','float64','int32','float32'].some(t => dsInfo.dtypes[c]?.includes(t))) || []
  const allCols = dsInfo?.columns || []

  const train = async () => {
    if (!datasetId || !targetCol) { toast.error('Select dataset and target column'); return }
    setLoading(true)
    try {
      const { data } = await predictionApi.train({ dataset_id: parseInt(datasetId), target_column: targetCol, model_type: modelType })
      setResult(data)
      toast.success('Model trained!')
    } catch (e) { toast.error(e.response?.data?.detail || 'Training failed') }
    finally { setLoading(false) }
  }

  const chartData = result?.forecast_data?.actual?.map((v, i) => ({
    i, actual: parseFloat(v?.toFixed(2)), predicted: parseFloat(result.forecast_data.predicted[i]?.toFixed(2))
  })) || []

  const featureData = Object.entries(result?.feature_importance || {}).slice(0, 10).map(([k, v]) => ({ name: k, value: v }))

  return (
    <Layout>
      <SectionHeader title="Predictions" description="Train ML models on your datasets" />
      <Card className="mb-6">
        <div className="flex flex-wrap gap-3">
          <select className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={datasetId} onChange={e => setDatasetId(e.target.value)}>
            <option value="">— Select Dataset —</option>
            {datasets?.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={targetCol} onChange={e => setTargetCol(e.target.value)}>
            <option value="">— Target Column —</option>
            {numCols.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={modelType} onChange={e => setModelType(e.target.value)}>
            <option value="linear">Linear Regression</option>
            <option value="random_forest">Random Forest</option>
            <option value="gradient_boost">Gradient Boosting</option>
          </select>
          <Button onClick={train} loading={loading}><Play className="w-4 h-4" /> Train Model</Button>
        </div>
      </Card>

      {result && (
        <div className="space-y-5 animate-fadein">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="R² Score" value={result.metrics.r2_score} icon={TrendingUp} color="#10b981" />
            <KpiCard label="RMSE" value={result.metrics.rmse} icon={TrendingUp} color="#6366f1" />
            <KpiCard label="MAE" value={result.metrics.mae} icon={TrendingUp} color="#f59e0b" />
            <KpiCard label="Test Samples" value={result.metrics.test_samples} icon={TrendingUp} color="#8b5cf6" />
          </div>

          {chartData.length > 0 && (
            <Card>
              <p className="text-sm font-semibold text-zinc-300 mb-3">Actual vs Predicted</p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="i" tick={{ fill: '#71717a', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#71717a', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="actual" stroke="#6366f1" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="predicted" stroke="#10b981" dot={false} strokeWidth={2} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}

          {featureData.length > 0 && (
            <Card>
              <p className="text-sm font-semibold text-zinc-300 mb-3">Feature Importance</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={featureData} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#71717a', fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#71717a', fontSize: 11 }} width={120} />
                  <Tooltip contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }} />
                  <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}
    </Layout>
  )
}

// ─── Simulation Page ───────────────────────────────────────────────────────────
import { simulationApi } from '../services/api'

export function SimulationPage() {
  const [vars, setVars] = useState([{ key: 'revenue', value: '100000' }, { key: 'growth_rate', value: '0.15' }])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const addVar = () => setVars(v => [...v, { key: '', value: '' }])
  const updateVar = (i, field, val) => setVars(v => v.map((x, j) => j === i ? { ...x, [field]: val } : x))

  const run = async () => {
    const variables = Object.fromEntries(vars.filter(v => v.key).map(v => [v.key, parseFloat(v.value) || 0]))
    setLoading(true)
    try {
      const { data } = await simulationApi.run({ variables, scenario_name: 'My Scenario' })
      setResult(data)
      toast.success('Simulation complete!')
    } catch { toast.error('Simulation failed') }
    finally { setLoading(false) }
  }

  return (
    <Layout>
      <SectionHeader title="What-If Simulation" description="Modify variables and compare scenarios" />
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <p className="text-sm font-semibold text-zinc-300 mb-4">Variables</p>
          <div className="space-y-2 mb-4">
            {vars.map((v, i) => (
              <div key={i} className="flex gap-2">
                <input placeholder="Variable name" value={v.key} onChange={e => updateVar(i, 'key', e.target.value)}
                  className="flex-1 bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500" />
                <input placeholder="Value" type="number" value={v.value} onChange={e => updateVar(i, 'value', e.target.value)}
                  className="w-28 bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500" />
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={addVar}>+ Add Variable</Button>
            <Button onClick={run} loading={loading}><Play className="w-4 h-4" /> Run Simulation</Button>
          </div>
        </Card>

        {result && (
          <Card className="animate-fadein">
            <p className="text-sm font-semibold text-zinc-300 mb-4">Results — {result.scenario_name}</p>
            <div className="space-y-3">
              {Object.entries(result.results).map(([key, vals]) => (
                <div key={key} className="bg-zinc-950 rounded-xl p-3">
                  <p className="text-xs font-semibold text-zinc-400 mb-2">{key}</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-center"><p className="text-zinc-500 mb-1">Base</p><p className="text-zinc-200 font-mono">{vals.base?.toLocaleString()}</p></div>
                    <div className="text-center"><p className="text-emerald-500 mb-1">Optimistic +{vals.delta_pct}%</p><p className="text-emerald-400 font-mono">{vals.optimistic?.toLocaleString()}</p></div>
                    <div className="text-center"><p className="text-red-500 mb-1">Pessimistic -{vals.delta_pct}%</p><p className="text-red-400 font-mono">{vals.pessimistic?.toLocaleString()}</p></div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </Layout>
  )
}

// ─── Anomaly Page ──────────────────────────────────────────────────────────────
import { anomalyApi } from '../services/api'

export function AnomalyPage() {
  const [datasetId, setDatasetId] = useState('')
  const [column, setColumn] = useState('')
  const [method, setMethod] = useState('zscore')
  const [threshold, setThreshold] = useState(2.5)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => datasetsApi.list().then(r => r.data) })
  const { data: dsInfo } = useQuery({
    queryKey: ['dsinfo', datasetId], enabled: !!datasetId,
    queryFn: () => datasetsApi.stats(datasetId).then(r => r.data),
  })

  const detect = async () => {
    if (!datasetId || !column) { toast.error('Select dataset and column'); return }
    setLoading(true)
    try {
      const { data } = await anomalyApi.detect(datasetId, column, method, threshold)
      setResult(data)
      toast.success(`Found ${data.anomaly_count} anomalies`)
    } catch (e) { toast.error(e.response?.data?.detail || 'Detection failed') }
    finally { setLoading(false) }
  }

  const numCols = dsInfo?.columns?.filter(c => ['int64','float64'].some(t => dsInfo.dtypes?.[c]?.includes(t))) || []

  return (
    <Layout>
      <SectionHeader title="Anomaly Detection" description="Detect spikes, drops, and outliers" />
      <Card className="mb-6">
        <div className="flex flex-wrap gap-3">
          <select className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={datasetId} onChange={e => setDatasetId(e.target.value)}>
            <option value="">— Dataset —</option>
            {datasets?.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={column} onChange={e => setColumn(e.target.value)}>
            <option value="">— Column —</option>
            {numCols.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={method} onChange={e => setMethod(e.target.value)}>
            <option value="zscore">Z-Score</option>
            <option value="iqr">IQR</option>
          </select>
          <input type="number" step="0.1" value={threshold} onChange={e => setThreshold(e.target.value)}
            placeholder="Threshold"
            className="w-28 bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500" />
          <Button onClick={detect} loading={loading}>Detect</Button>
        </div>
      </Card>

      {result && (
        <div className="space-y-4 animate-fadein">
          <div className="grid grid-cols-3 gap-4">
            <KpiCard label="Total Rows" value={result.total_rows?.toLocaleString()} icon={TrendingUp} color="#6366f1" />
            <KpiCard label="Anomalies" value={result.anomaly_count} icon={TrendingUp} color="#ef4444" />
            <KpiCard label="Anomaly %" value={`${result.anomaly_pct}%`} icon={TrendingUp} color="#f59e0b" />
          </div>
          {result.anomalies?.length > 0 && (
            <Card>
              <p className="text-sm font-semibold text-zinc-300 mb-3">Anomalous Records (top 50)</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-500">
                      {Object.keys(result.anomalies[0]).slice(0, 6).map(k => <th key={k} className="text-left py-2 pr-4">{k}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {result.anomalies.map((row, i) => (
                      <tr key={i} className="border-b border-zinc-800/40 hover:bg-zinc-800/30">
                        {Object.values(row).slice(0, 6).map((v, j) => <td key={j} className="py-1.5 pr-4 text-zinc-300 font-mono">{String(v)}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}
    </Layout>
  )
}

// ─── History Page ──────────────────────────────────────────────────────────────
import { historyApi } from '../services/api'
import { Clock } from 'lucide-react'

export function HistoryPage() {
  const { data, isLoading } = useQuery({ queryKey: ['history'], queryFn: () => historyApi.get().then(r => r.data) })

  return (
    <Layout>
      <SectionHeader title="Query History" description="All your past AI queries" />
      {isLoading ? <div className="flex justify-center py-12"><Spinner /></div>
        : !data?.length ? <EmptyState icon={Clock} title="No history yet" description="Your AI queries will appear here" />
        : (
          <div className="space-y-3">
            {data.map(h => (
              <Card key={h.id} className="hover:border-zinc-700 transition-all">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-200 mb-1">{h.query}</p>
                    <p className="text-xs text-zinc-500 line-clamp-2">{h.response}</p>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <p className="text-xs text-zinc-500">{new Date(h.created_at).toLocaleDateString()}</p>
                    <p className="text-xs text-zinc-600 mt-0.5">{h.model_used?.split('/')[1]}</p>
                    <p className="text-xs text-zinc-600">{h.latency_ms?.toFixed(0)}ms</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
    </Layout>
  )
}

// ─── Export Page ───────────────────────────────────────────────────────────────
import { exportApi } from '../services/api'
import { Download, FileSpreadsheet } from 'lucide-react'

export function ExportPage() {
  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => datasetsApi.list().then(r => r.data) })
  const [dlLoading, setDlLoading] = useState({})

  const download = async (id, type) => {
    setDlLoading(prev => ({ ...prev, [`${id}-${type}`]: true }))
    try {
      const res = type === 'excel' ? await exportApi.excel(id) : await exportApi.csv(id)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url; a.download = `export.${type === 'excel' ? 'xlsx' : 'csv'}`; a.click()
      URL.revokeObjectURL(url)
      toast.success('Downloaded!')
    } catch { toast.error('Export failed') }
    finally { setDlLoading(prev => ({ ...prev, [`${id}-${type}`]: false })) }
  }

  return (
    <Layout>
      <SectionHeader title="Export" description="Download your datasets and reports" />
      {!datasets?.length ? <EmptyState icon={Download} title="No datasets" description="Upload a dataset to export" />
        : (
          <div className="grid gap-3">
            {datasets.map(ds => (
              <Card key={ds.id} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-200">{ds.name}</p>
                  <p className="text-xs text-zinc-500">{ds.rows?.toLocaleString()} rows</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" loading={dlLoading[`${ds.id}-csv`]} onClick={() => download(ds.id, 'csv')}>
                    <Download className="w-4 h-4" /> CSV
                  </Button>
                  <Button variant="secondary" size="sm" loading={dlLoading[`${ds.id}-excel`]} onClick={() => download(ds.id, 'excel')}>
                    <FileSpreadsheet className="w-4 h-4" /> Excel
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
    </Layout>
  )
}

// ─── Evaluation Page ───────────────────────────────────────────────────────────
import { evalApi } from '../services/api'
import { Brain } from 'lucide-react'

export function EvaluationPage() {
  const { data, isLoading } = useQuery({ queryKey: ['eval-dashboard'], queryFn: () => evalApi.dashboard().then(r => r.data) })

  const scores = data?.avg_scores || {}
  const scoreItems = [
    { label: 'Context Recall', key: 'context_recall', color: '#6366f1' },
    { label: 'Context Precision', key: 'context_precision', color: '#8b5cf6' },
    { label: 'Faithfulness', key: 'faithfulness', color: '#10b981' },
    { label: 'Answer Relevancy', key: 'answer_relevancy', color: '#f59e0b' },
  ]

  return (
    <Layout>
      <SectionHeader title="AI Evaluation" description="Ragas-powered response quality metrics" />
      {isLoading ? <div className="flex justify-center py-12"><Spinner /></div>
        : !data?.total_evaluations ? <EmptyState icon={Brain} title="No evaluations yet" description="Run AI queries and evaluate them to see scores" />
        : (
          <div className="space-y-5 animate-fadein">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {scoreItems.map(({ label, key, color }) => (
                <KpiCard key={key} label={label} value={`${((scores[key] || 0) * 100).toFixed(1)}%`}
                  sub={`${data.total_evaluations} evals`} icon={Brain} color={color} />
              ))}
            </div>
            <Card>
              <p className="text-sm font-semibold text-zinc-300 mb-4">Score Breakdown</p>
              <div className="space-y-3">
                {scoreItems.map(({ label, key, color }) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-zinc-400">{label}</span>
                      <span className="text-zinc-300 font-mono">{((scores[key] || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${(scores[key] || 0) * 100}%`, background: color }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}
    </Layout>
  )
}

// ─── Monitoring Page ───────────────────────────────────────────────────────────
import { monitorApi } from '../services/api'
import { Activity } from 'lucide-react'

export function MonitoringPage() {
  const { data: summary } = useQuery({ queryKey: ['monitor-summary'], queryFn: () => monitorApi.summary().then(r => r.data) })
  const { data: logs } = useQuery({ queryKey: ['monitor-logs'], queryFn: () => monitorApi.logs().then(r => r.data) })

  return (
    <Layout>
      <SectionHeader title="Monitoring" description="API usage, latency, and error tracking" />
      {summary?.total_requests && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <KpiCard label="Total Requests" value={summary.total_requests?.toLocaleString()} icon={Activity} color="#6366f1" />
          <KpiCard label="Error Count" value={summary.error_count} icon={Activity} color="#ef4444" />
          <KpiCard label="Error Rate" value={`${summary.error_rate_pct}%`} icon={Activity} color="#f59e0b" />
          <KpiCard label="Avg Latency" value={`${summary.avg_latency_ms?.toFixed(0)}ms`} icon={Activity} color="#10b981" />
        </div>
      )}
      {logs?.length > 0 && (
        <Card>
          <p className="text-sm font-semibold text-zinc-300 mb-3">Recent Requests</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500">
                  <th className="text-left py-2 pr-4">Endpoint</th>
                  <th className="text-left py-2 pr-4">Method</th>
                  <th className="text-left py-2 pr-4">Status</th>
                  <th className="text-left py-2 pr-4">Latency</th>
                  <th className="text-left py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(l => (
                  <tr key={l.id} className="border-b border-zinc-800/40 hover:bg-zinc-800/30">
                    <td className="py-1.5 pr-4 text-zinc-300 font-mono">{l.endpoint}</td>
                    <td className="py-1.5 pr-4 text-zinc-400">{l.method}</td>
                    <td className="py-1.5 pr-4">
                      <span className={`font-mono ${l.status_code < 400 ? 'text-emerald-400' : 'text-red-400'}`}>{l.status_code}</span>
                    </td>
                    <td className="py-1.5 pr-4 text-zinc-400 font-mono">{l.latency_ms?.toFixed(0)}ms</td>
                    <td className="py-1.5 text-zinc-500">{new Date(l.created_at).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </Layout>
  )
}

// ─── Admin Page ────────────────────────────────────────────────────────────────
import { adminApi } from '../services/api'
import { Shield } from 'lucide-react'

export function AdminPage() {
  const { data: stats } = useQuery({ queryKey: ['admin-stats'], queryFn: () => adminApi.stats().then(r => r.data) })
  const { data: users } = useQuery({ queryKey: ['admin-users'], queryFn: () => adminApi.users().then(r => r.data) })

  return (
    <Layout>
      <SectionHeader title="Admin Dashboard" description="System overview and user management" />
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <KpiCard label="Total Users" value={stats.total_users} icon={Shield} color="#6366f1" />
          <KpiCard label="Datasets" value={stats.total_datasets} icon={Shield} color="#8b5cf6" />
          <KpiCard label="AI Queries" value={stats.total_queries} icon={Shield} color="#10b981" />
        </div>
      )}
      {users?.length > 0 && (
        <Card>
          <p className="text-sm font-semibold text-zinc-300 mb-3">Users</p>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500">
                <th className="text-left py-2 pr-4">ID</th>
                <th className="text-left py-2 pr-4">Email</th>
                <th className="text-left py-2 pr-4">Username</th>
                <th className="text-left py-2 pr-4">Role</th>
                <th className="text-left py-2">Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b border-zinc-800/40">
                  <td className="py-1.5 pr-4 text-zinc-400 font-mono">{u.id}</td>
                  <td className="py-1.5 pr-4 text-zinc-300">{u.email}</td>
                  <td className="py-1.5 pr-4 text-zinc-300">{u.username}</td>
                  <td className="py-1.5 pr-4"><span className={`px-2 py-0.5 rounded text-[10px] font-medium ${u.role === 'admin' ? 'bg-brand-900/50 text-brand-400' : 'bg-zinc-800 text-zinc-400'}`}>{u.role}</span></td>
                  <td className="py-1.5"><span className={u.is_active ? 'text-emerald-400' : 'text-red-400'}>{u.is_active ? '✓' : '✗'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </Layout>
  )
}

// ─── Graph Page ────────────────────────────────────────────────────────────────
import { graphApi } from '../services/api'
import { GitFork } from 'lucide-react'

export function GraphPage() {
  const [query, setQuery] = useState('MATCH (n) RETURN n LIMIT 25')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const { data: stats } = useQuery({ queryKey: ['graph-stats'], queryFn: () => graphApi.stats().then(r => r.data).catch(() => null) })

  const runQuery = async () => {
    setLoading(true)
    try {
      const { data } = await graphApi.query({ cypher: query })
      setResult(data)
    } catch (e) { toast.error(e.response?.data?.detail || 'Query failed') }
    finally { setLoading(false) }
  }

  return (
    <Layout>
      <SectionHeader title="Graph Explorer" description="Query and explore your Neo4j knowledge graph" />
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <KpiCard label="Nodes" value={stats.nodes?.toLocaleString()} icon={GitFork} color="#6366f1" />
          <KpiCard label="Relationships" value={stats.relationships?.toLocaleString()} icon={GitFork} color="#8b5cf6" />
          <KpiCard label="Labels" value={stats.labels?.length || 0} icon={GitFork} color="#10b981" />
        </div>
      )}
      <Card className="mb-4">
        <p className="text-xs font-semibold text-zinc-500 mb-2">Cypher Query</p>
        <textarea value={query} onChange={e => setQuery(e.target.value)} rows={3}
          className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-sm font-mono text-zinc-100 focus:outline-none focus:border-brand-500 mb-3 resize-none" />
        <Button onClick={runQuery} loading={loading}>Run Query</Button>
      </Card>
      {result && (
        <Card className="animate-fadein">
          <p className="text-sm font-semibold text-zinc-300 mb-3">{result.count} Results</p>
          <pre className="text-xs text-zinc-400 bg-zinc-950 rounded-lg p-4 overflow-x-auto max-h-80">
            {JSON.stringify(result.results, null, 2)}
          </pre>
        </Card>
      )}
    </Layout>
  )
}
