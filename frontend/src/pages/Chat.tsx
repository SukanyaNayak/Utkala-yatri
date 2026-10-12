import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'

type Msg = { role: 'user' | 'assistant'; content: string }

export default function Chat() {
  const { t, i18n } = useTranslation()
  const [history, setHistory] = useState<Msg[]>([])
  const [input, setInput] = useState(''); const [busy, setBusy] = useState(false)
  const [recording, setRecording] = useState(false)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const lang = i18n.language === 'or' ? 'or' : i18n.language === 'hi' ? 'hi' : 'en'

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [history])

  async function send(text: string) {
    if (!text.trim()) return
    const mine: Msg = { role: 'user', content: text }
    const next = [...history, mine]
    setHistory(next); setInput(''); setBusy(true)
    try {
      const { reply } = await api.chat(next.map(m => ({ role: m.role, content: m.content })), lang)
      setHistory([...next, { role: 'assistant', content: reply }])
    } catch { setHistory([...next, { role: 'assistant', content: '⚠️ Service busy — try again.' }]) }
    setBusy(false)
  }

  async function toggleRec() {
    if (recording) { mediaRef.current?.stop(); setRecording(false); return }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const rec = new MediaRecorder(stream)
    chunksRef.current = []
    rec.ondataavailable = e => chunksRef.current.push(e.data)
    rec.onstop = async () => {
      stream.getTracks().forEach(tr => tr.stop())
      const blob = new Blob(chunksRef.current, { type: 'audio/wav' })
      try { const { text } = await api.transcribe(blob); send(text) }
      catch { alert('Could not hear that clearly — try again or type.') }
    }
    rec.start(); mediaRef.current = rec; setRecording(true)
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      <h1 className="text-3xl font-bold mb-2">🤖 {t('nav_chat')}</h1>
      <div className="flex-1 overflow-y-auto space-y-3 mb-3">
        {history.length === 0 && <p className="text-gray-500">{t('try_these')}</p>}
        {history.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 whitespace-pre-wrap ${m.role === 'user' ? 'bg-terracotta text-white' : 'bg-white border'}`}>
              {m.content}
              {m.role === 'assistant' && (
                <audio controls src={api.ttsUrl(m.content, lang)} className="mt-2 w-64 h-8" />)}
            </div>
          </div>))}
        {busy && <p className="text-gray-400">🤖 …</p>}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <button onClick={toggleRec} className={`btn-primary ${recording ? 'animate-pulse' : ''}`}>{recording ? '⏹' : '🎙️'}</button>
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send(input)}
          placeholder={t('chat_input_ph')} className="flex-1 rounded-lg border p-2 bg-white" />
        <button onClick={() => send(input)} className="btn-primary">➤</button>
      </div>
    </div>)
}