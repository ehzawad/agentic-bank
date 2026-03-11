import { useEffect, useRef, useState } from 'react'
import { createSession, sendMessage, type ChatResponse } from './api'
import './App.css'

interface Message {
  role: 'user' | 'bot'
  text: string
  meta?: {
    state: string
    emotion: string
    tools: string[]
    transferred: boolean
  }
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    createSession()
      .then((s) => {
        setSessionId(s.session_id)
        setMessages([{ role: 'bot', text: s.greeting }])
      })
      .catch(() => setError('Cannot connect to backend. Is it running on :8000?'))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!sessionId || !input.trim() || loading) return
    const text = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text }])
    setLoading(true)
    setError(null)

    try {
      const res: ChatResponse = await sendMessage(sessionId, text)
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          text: res.response,
          meta: {
            state: res.state,
            emotion: res.emotion,
            tools: res.tool_calls.map((tc) => tc.tool),
            transferred: res.transferred_to_human,
          },
        },
      ])
    } catch {
      setError('Failed to get response')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const restart = async () => {
    try {
      const s = await createSession()
      setSessionId(s.session_id)
      setMessages([{ role: 'bot', text: s.greeting }])
      setError(null)
    } catch {
      setError('Cannot connect to backend')
    }
  }

  return (
    <div className="shell">
      <header className="header">
        <h1 className="logo">Agentic Bank</h1>
        <div className="header-right">
          {sessionId && <code className="sid">{sessionId.slice(0, 8)}</code>}
          <button className="btn-ghost" onClick={restart}>New Session</button>
        </div>
      </header>

      <main className="chat-area">
        {messages.map((m, i) => (
          <div key={i} className={`msg-row ${m.role}`}>
            <div className={`bubble ${m.role}`}>
              <p className="bubble-text">{m.text}</p>
              {m.meta && (
                <div className="meta">
                  <span className="tag state">{m.meta.state}</span>
                  {m.meta.emotion !== 'neutral' && (
                    <span className="tag emotion">{m.meta.emotion}</span>
                  )}
                  {m.meta.tools.map((t, j) => (
                    <span key={j} className="tag tool">{t}</span>
                  ))}
                  {m.meta.transferred && (
                    <span className="tag transfer">HUMAN TRANSFER</span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="msg-row bot">
            <div className="bubble bot thinking">Thinking...</div>
          </div>
        )}

        {error && <div className="err">{error}</div>}
        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <input
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Type a message..."
          disabled={loading}
        />
        <button
          className="btn-send"
          onClick={send}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </footer>
    </div>
  )
}
