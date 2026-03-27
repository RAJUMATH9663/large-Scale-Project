import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { datasetsApi, dashboardApi } from '../services/api'
import { KpiCard, Card, Select, Button, Spinner, EmptyState, SectionHeader } from '../components/UI'
import Layout from '../components/Layout'
import { BarChart3, TrendingUp, Database, Activity, RefreshCw, ImageIcon } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'

export default function DashboardPage() {
  const [searchParams] = useSearchParams()
  const [selectedDataset, setSelectedDataset] = useState(searchParams.get('dataset') || '')
  const [chartType, setChartType] = useState('histogram')
  const [selectedCol, setSelectedCol] = useState('')
  const [selectedX, setSelectedX] = useState('')
  const [selectedY, setSelectedY] = useState('')
  const [chartImg, setChartImg] = useState(null)
  const [chartLoading, setChartLoading] = useState(false)

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => datasetsApi.list().then(r => r.data) })
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard', selectedDataset],
    queryFn: () => dashboardApi.get(selectedDataset).then(r => r.data),
    enabled: !!selectedDataset,
  })

  const loadChart = async () => {
    if (!selectedDataset) return
    setChartLoading(true)
    setChartImg(null)
    try {
      let res
      if (chartType === 'histogram' && selectedCol) {
        res = await dashboardApi.histogram(selectedDataset, selectedCol)
      } else if (chartType === 'scatter' && selectedX && selectedY) {
        res = await dashboardApi.scatter(selectedDataset, selectedX, selectedY)
      } else if (chartType === 'correlation') {
        res = await dashboardApi.correlation(selectedDataset)
      } else if (chartType === 'bar' && selectedX && selectedY) {
        res = await dashboardApi.bar(selectedDataset, selectedX, selectedY)
      }
      if (res?.data?.image) setChartImg(res.data.image)
    } catch (e) { console.error(e) }
    finally { setChartLoading(false) }
  }

  const kpis = dashboard?.kpis || {}
  const kpiEntries = Object.entries(kpis).slice(0, 4)
  const colOptions = dashboard?.all_columns?.map(c => ({ value: c, label: c })) || []
  const numColOptions = dashboard?.numeric_columns?.map(c => ({ value: c, label: c })) || []

  return (
    <Layout>
      <SectionHeader title="Dashboard" description="Explore your data with charts and KPIs" />

      {/* Dataset Selector */}
      <div className="flex items-center gap-3 mb-6">
        <select className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
          value={selectedDataset} onChange={e => setSelectedDataset(e.target.value)}>
          <option value="">— Select a dataset —</option>
          {datasets?.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>

      {!selectedDataset ? (
        <EmptyState icon={Database} title="Select a dataset" description="Choose a dataset above to see KPIs and charts" />
      ) : isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : (
        <div className="space-y-6 animate-fadein">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard label="Total Rows" value={dashboard?.rows?.toLocaleString()} icon={Database} color="#6366f1" />
            <KpiCard label="Columns" value={dashboard?.columns} icon={BarChart3} color="#8b5cf6" />
            {kpiEntries[0] && <KpiCard label={kpiEntries[0][0]} value={kpiEntries[0][1].sum?.toLocaleString()} sub="sum" icon={TrendingUp} color="#10b981" />}
            {kpiEntries[1] && <KpiCard label={kpiEntries[1][0]} value={kpiEntries[1][1].mean?.toLocaleString()} sub="mean" icon={Activity} color="#f59e0b" />}
          </div>

          {/* KPI Detail Table */}
          {kpiEntries.length > 0 && (
            <Card>
              <p className="text-sm font-semibold text-zinc-300 mb-3">Column Statistics</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-zinc-500 border-b border-zinc-800">
                      <th className="text-left py-2 pr-4">Column</th>
                      <th className="text-right py-2 px-3">Sum</th>
                      <th className="text-right py-2 px-3">Mean</th>
                      <th className="text-right py-2 px-3">Max</th>
                      <th className="text-right py-2 px-3">Min</th>
                    </tr>
                  </thead>
                  <tbody>
                    {kpiEntries.map(([col, stats]) => (
                      <tr key={col} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                        <td className="py-2 pr-4 font-medium text-zinc-300">{col}</td>
                        <td className="text-right py-2 px-3 text-zinc-400 font-mono">{stats.sum?.toLocaleString()}</td>
                        <td className="text-right py-2 px-3 text-zinc-400 font-mono">{stats.mean?.toLocaleString()}</td>
                        <td className="text-right py-2 px-3 text-zinc-400 font-mono">{stats.max?.toLocaleString()}</td>
                        <td className="text-right py-2 px-3 text-zinc-400 font-mono">{stats.min?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Chart Generator */}
          <Card>
            <p className="text-sm font-semibold text-zinc-300 mb-4">Chart Generator</p>
            <div className="flex flex-wrap gap-3 mb-4">
              <Select label="Chart Type" value={chartType} onChange={e => setChartType(e.target.value)}
                options={[
                  { value: 'histogram', label: 'Histogram' },
                  { value: 'bar', label: 'Bar Chart' },
                  { value: 'scatter', label: 'Scatter Plot' },
                  { value: 'correlation', label: 'Correlation Heatmap' },
                ]} />
              {(chartType === 'histogram') && (
                <Select label="Column" value={selectedCol} onChange={e => setSelectedCol(e.target.value)} options={[{ value: '', label: '—' }, ...numColOptions]} />
              )}
              {(chartType === 'scatter' || chartType === 'bar') && (<>
                <Select label="X Column" value={selectedX} onChange={e => setSelectedX(e.target.value)} options={[{ value: '', label: '—' }, ...colOptions]} />
                <Select label="Y Column" value={selectedY} onChange={e => setSelectedY(e.target.value)} options={[{ value: '', label: '—' }, ...numColOptions]} />
              </>)}
              <div className="flex items-end">
                <Button onClick={loadChart} loading={chartLoading} size="md">
                  <RefreshCw className="w-4 h-4" /> Generate
                </Button>
              </div>
            </div>

            {chartLoading && <div className="flex justify-center py-12"><Spinner /></div>}
            {chartImg && <img src={chartImg} alt="chart" className="rounded-lg w-full" />}
            {!chartImg && !chartLoading && (
              <div className="flex flex-col items-center py-10 text-zinc-600">
                <ImageIcon className="w-10 h-10 mb-2" />
                <p className="text-sm">Select options and click Generate</p>
              </div>
            )}
          </Card>

          {/* Missing Values */}
          {dashboard?.missing_values && (
            <Card>
              <p className="text-sm font-semibold text-zinc-300 mb-3">Missing Values</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Object.entries(dashboard.missing_values).map(([col, count]) => (
                  <div key={col} className="flex justify-between items-center bg-zinc-800/50 rounded-lg px-3 py-2">
                    <span className="text-xs text-zinc-400 truncate mr-2">{col}</span>
                    <span className={`text-xs font-mono font-bold ${count > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </Layout>
  )
}
