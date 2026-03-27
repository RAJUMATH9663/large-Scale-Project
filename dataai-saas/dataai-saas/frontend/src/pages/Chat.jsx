import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { aiApi, datasetsApi } from '../services/api'
import { Button, Card, Select, Spinner } from '../components/UI'
import Layout from '../components/Layout'
import toast from 'react-hot-toast'
import { Send, Bot, User, Zap, Brain } from 'lucide-react'
import clsx from 'clsx'

const SAMPLE_QUERIES = [
  'What are the key trends in this dataset?',
  'Explain the top correlations in the data',
  'What anomalies should I be aware of?',
  'Write a business story about this data',
  'What predictions can you make?',
]

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState('')
  const [selectedModel, setSelectedModel] = useState('openai/gpt-4o-mini')
  const bottomRef = useRef(null)

  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => datasetsApi.list().then(r => r.data) })
  const { data: models } = useQuery({ queryKey: ['models'], queryFn: () => aiApi.models().then(r => r.data) })

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (queryText) => {
    const q = queryText || input.trim()
    if (!q || loading) return
    setInput('')
    const userMsg = { role: 'user', content: q, id: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const { data } = await aiApi.query({
        query: q,
        dataset_id: selectedDataset ? parseInt(selectedDataset) : null,
        model: selectedModel,
      })
      setMessages(prev => [...prev, {
        role: 'assistant', content: data.response,
        meta: { intent: data.intent, model: data.model, tokens: data.tokens_used, latency: data.latency_ms },
        id: Date.now() + 1,
      }])
    } catch (err) {
      toast.error('AI query failed')
      setMessages(prev => [...prev, { role: 'error', content: 'Failed to get response. Please try again.', id: Date.now() + 1 }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="flex flex-col h-[calc(100vh-96px)]">
        {/* Header Controls */}
        <div className="flex items-center gap-3 mb-4 flex-shrink-0">
          <select className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={selectedDataset} onChange={e => setSelectedDataset(e.target.value)}>
            <option value="">No dataset (general AI)</option>
            {datasets?.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-brand-500"
            value={selectedModel} onChange={e => setSelectedModel(e.target.value)}>
            {(models?.models || ['openai/gpt-4o-mini']).map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {!messages.length && (
            <div className="flex flex-col items-center py-12 gap-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-brand-500/30">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold font-display text-zinc-200">DataAI Assistant</p>
                <p className="text-sm text-zinc-500 mt-1">Ask anything about your data</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full max-w-xl">
                {SAMPLE_QUERIES.map(q => (
                  <button key={q} onClick={() => send(q)}
                    className="text-left text-xs text-zinc-400 bg-zinc-900 border border-zinc-800 hover:border-brand-500/50 hover:text-brand-400 px-3 py-2.5 rounded-xl transition-all">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={clsx('flex gap-3 animate-fadein', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
              {msg.role !== 'user' && (
                <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              <div className={clsx('max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-brand-600 text-white rounded-tr-sm'
                  : msg.role === 'error'
                  ? 'bg-red-900/40 border border-red-800 text-red-300'
                  : 'bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-tl-sm')}>
                <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
                {msg.meta && (
                  <div className="flex gap-3 mt-2 pt-2 border-t border-zinc-700 text-[10px] text-zinc-500">
                    <span>🎯 {msg.meta.intent}</span>
                    <span>🤖 {msg.meta.model?.split('/')[1]}</span>
                    <span>⚡ {msg.meta.latency?.toFixed(0)}ms</span>
                    {msg.meta.tokens > 0 && <span>🔤 {msg.meta.tokens} tokens</span>}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-zinc-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-zinc-300" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 animate-fadein">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                <Spinner className="w-4 h-4" />
                <span className="text-sm text-zinc-400">Analyzing...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="flex-shrink-0 flex gap-2">
          <input
            value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about your data..."
            className="flex-1 bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
          <Button onClick={() => send()} loading={loading} className="px-4">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Layout>
  )
}
