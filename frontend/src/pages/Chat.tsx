export const HERO_IMAGE = "/hero.jpg"; // put hero.jpg in frontend/public/ — or paste an https:// URL
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import PageHero from '../components/PageHero'
import { FaLandmark, FaUmbrellaBeach, FaWater, FaGopuram } from 'react-icons/fa'


type Msg = { role: 'user' | 'assistant'; content: string }

export default function Chat() {
  const { t, i18n } = useTranslation()
  const [history, setHistory] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
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
    setHistory(next)
    setInput('')
    setBusy(true)
    try {
      const { reply } = await api.chat(
        next.map(m => ({ role: m.role, content: m.content })), lang)
      setHistory([...next, { role: 'assistant', content: reply }])
    } catch {
      setHistory([...next, { role: 'assistant', content: '⚠️ Service busy — try again.' }])
    }
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
      catch { alert(t('not_heard')) }
    }
    rec.start()
    mediaRef.current = rec
    setRecording(true)
  }
return (
  <div>
    {/* ── Full-width banner (same as every page) ── */}
    <PageHero title={t('chat_title')} desc={t('chat_desc')} quote={t('chat_quote')} />

    {/* ── Centered chat column below the banner ── */}
    <div className="mx-auto flex h-[calc(100vh-16rem)] min-h-[22rem] max-w-3xl flex-col px-4">
  
        <div className="mb-3 flex-1 space-y-3 overflow-y-auto">
          {/* cold-start: pastel quick-question cards (clicking sends the question) */}
          {!history || history.length === 0 ? (
            <div className="py-2">
              <h2 className="font-script text-4xl text-forest">✨ {t('chat_try')}</h2>
              <p className="mb-4 text-sm text-gray-500">{t('chat_try_sub')}</p>
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  { q: t('chat_q1'), icon: FaLandmark, bg: 'bg-[#E7EFD9]', badge: 'bg-[#CFE3BC]' },
                  { q: t('chat_q2'), icon: FaUmbrellaBeach, bg: 'bg-[#FCE9CB]', badge: 'bg-[#F7D6A4]' },
                  { q: t('chat_q3'), icon: FaWater, bg: 'bg-[#D9E9F2]', badge: 'bg-[#B9D8E8]' },
                  { q: t('chat_q4'), icon: FaGopuram, bg: 'bg-[#EAE0F1]', badge: 'bg-[#D8C6E6]' },
                ].map((c, i) => (
                  <button key={i} onClick={() => send(c.q)}
                    className={`flex items-center gap-3 rounded-2xl p-3 pr-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${c.bg}`}>
                    <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-forest ${c.badge}`}>
                      <c.icon size={20} />
                    </span>
                    <span className="flex-1 text-sm font-semibold leading-snug text-[#3E2A1B]">
                      {c.q}
                    </span>
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-forest text-sm text-white">
                      ›
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            history.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-2xl px-4 py-2 whitespace-pre-wrap ${
                  m.role === 'user' ? 'bg-terracotta text-white' : 'bg-white border'
                }`}>
                  {m.content}
                  {m.role === 'assistant' && (
                    <audio controls src={api.ttsUrl(m.content, lang)} className="mt-2 h-8 w-64" />
                  )}
                </div>
              </div>
            ))
          )}
          {busy && <p className="text-gray-400">🤖 …</p>}
          <div ref={bottomRef} />
        </div>

        <div className="flex gap-2">
          <button onClick={toggleRec}
            className={`btn-primary ${recording ? 'animate-pulse' : ''}`}>
            {recording ? '⏹' : '🎙️'}
          </button>
          <input
            value={input}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && send(input)}
            placeholder={t('chat_input_ph')}
            className="flex-1 rounded-lg border p-2 bg-white"
          />
          <button onClick={() => send(input)} className="btn-primary">➤</button>
        </div>

        {/* hint bar */}
        <p className="mt-3 rounded-2xl bg-sage px-4 py-3 text-center text-xs text-[#3E2A1B]">
          📍 {t('chat_hint')}
        </p>
      </div>
    </div>
  )
}