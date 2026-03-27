import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { datasetsApi } from '../services/api'
import { Button, Card, Badge, EmptyState, SectionHeader, Spinner } from '../components/UI'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import { Upload, Database, Trash2, BarChart2, FileText, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export default function DatasetsPage() {
  const [uploading, setUploading] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => datasetsApi.list().then((r) => r.data),
  })

  const onDrop = useCallback(async (files) => {
    if (!files.length) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', files[0])
    try {
      await datasetsApi.upload(formData)
      toast.success('Dataset uploaded successfully!')
      queryClient.invalidateQueries(['datasets'])
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [queryClient])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'text/csv': ['.csv'], 'application/pdf': ['.pdf'] }, maxFiles: 1,
  })

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    try {
      await datasetsApi.delete(id)
      toast.success('Dataset deleted')
      queryClient.invalidateQueries(['datasets'])
    } catch { toast.error('Delete failed') }
  }

  return (
    <Layout>
      <SectionHeader title="Datasets" description="Upload and manage your data files"
        action={<Button variant="ghost" size="sm" onClick={() => queryClient.invalidateQueries(['datasets'])}>
          <RefreshCw className="w-4 h-4" />
        </Button>} />

      {/* Upload Zone */}
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-10 mb-8 text-center cursor-pointer transition-all
        ${isDragActive ? 'border-brand-500 bg-brand-500/5' : 'border-zinc-700 hover:border-zinc-600 hover:bg-zinc-900/50'}`}>
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center">
            {uploading ? <Spinner /> : <Upload className="w-6 h-6 text-zinc-400" />}
          </div>
          <div>
            <p className="text-sm font-medium text-zinc-300">
              {uploading ? 'Uploading...' : isDragActive ? 'Drop file here' : 'Drop CSV or PDF here'}
            </p>
            <p className="text-xs text-zinc-500 mt-1">or click to browse · Max 50MB</p>
          </div>
        </div>
      </div>

      {/* Dataset List */}
      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : !data?.length ? (
        <EmptyState icon={Database} title="No datasets yet" description="Upload a CSV or PDF to get started" />
      ) : (
        <div className="grid gap-3">
          {data.map((ds) => (
            <Card key={ds.id}
              className="flex items-center gap-4 hover:border-zinc-700 cursor-pointer transition-all"
              onClick={() => navigate(`/dashboard?dataset=${ds.id}`)}>
              <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
                {ds.file_type === 'pdf' ? <FileText className="w-5 h-5 text-amber-400" /> : <Database className="w-5 h-5 text-brand-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-200 truncate">{ds.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {ds.rows?.toLocaleString()} rows · {ds.columns} cols · v{ds.version || 1}
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <Badge variant={ds.status === 'ready' ? 'success' : 'warning'}>{ds.status}</Badge>
                <Button variant="ghost" size="sm" onClick={(e) => handleDelete(ds.id, e)}>
                  <Trash2 className="w-4 h-4 text-zinc-500 hover:text-red-400" />
                </Button>
                <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/dashboard?dataset=${ds.id}`) }}>
                  <BarChart2 className="w-4 h-4 text-zinc-500 hover:text-brand-400" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  )
}
