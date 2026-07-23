import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import { api } from '../api/client'

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

const suggestedQuestions = [
  'Jam buka perpustakaan',
  'Cara pinjam buku',
  'Fasilitas perpustakaan',
  'Lokasi perpustakaan',
]

export default function ChatDemo() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId] = useState(generateSessionId)
  const [typing, setTyping] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text) {
    const msg = (text || input).trim()
    if (!msg) return

    setShowWelcome(false)
    setInput('')
    setMessages((prev) => [...prev, { text: msg, sender: 'user' }])
    setTyping(true)

    try {
      const data = await api('/chat/message', {
        method: 'POST',
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      })
      setMessages((prev) => [
        ...prev,
        {
          text: data.message,
          sender: 'bot',
          quickReplies: data.quick_replies || [],
          intent: data.intent,
          confidence: data.confidence,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          text: 'Maaf, terjadi kesalahan. Pastikan backend sudah berjalan.',
          sender: 'bot',
          quickReplies: [],
        },
      ])
    } finally {
      setTyping(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') sendMessage()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-500 to-primary-800 flex items-center justify-center p-4">
      <div className="w-full max-w-lg h-[700px] bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-500 to-primary-700 text-white px-6 py-5 flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-bold text-lg">Tanya Perpustakaan</h2>
            <p className="text-sm text-white/80">BPK RI • Online 24/7</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-gray-50">
          {showWelcome && (
            <div className="text-center py-8">
              <Sparkles className="w-16 h-16 text-primary-300 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-700 mb-2">Selamat Datang!</h3>
              <p className="text-sm text-gray-500 mb-6">
                Saya siap membantu Anda dengan informasi seputar Perpustakaan BPK RI
              </p>
              <div className="space-y-2">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-700 hover:border-primary-500 hover:bg-primary-50 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i}>
              <div className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.sender === 'bot'
                      ? 'bg-gradient-to-br from-primary-500 to-primary-700 text-white'
                      : 'bg-green-500 text-white'
                  }`}
                >
                  {msg.sender === 'bot' ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                </div>
                <div
                  className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm ${
                    msg.sender === 'bot'
                      ? 'bg-white text-gray-800 shadow-sm rounded-bl-sm'
                      : 'bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-br-sm'
                  }`}
                >
                  <div dangerouslySetInnerHTML={{ __html: formatText(msg.text) }} />
                  {msg.sender === 'bot' && msg.intent && (
                    <div className="mt-2 text-xs text-primary-500 bg-primary-50 rounded-full px-2 py-0.5 inline-block">
                      {msg.intent} · {Math.round((msg.confidence || 0) * 100)}%
                    </div>
                  )}
                </div>
              </div>
              {msg.quickReplies?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2 ml-11">
                  {msg.quickReplies.map((qr) => (
                    <button
                      key={qr}
                      onClick={() => sendMessage(qr)}
                      className="px-4 py-1.5 bg-white border-2 border-primary-500 text-primary-600 rounded-full text-xs font-medium hover:bg-primary-500 hover:text-white transition-all"
                    >
                      {qr}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {typing && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white px-5 py-3 rounded-2xl rounded-bl-sm shadow-sm flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-6 py-4 bg-white border-t border-gray-100">
          <div className="flex gap-3 items-center bg-gray-50 rounded-full px-5 py-2 border-2 border-transparent focus-within:border-primary-500 focus-within:bg-white transition-all">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ketik pertanyaan Anda..."
              className="flex-1 bg-transparent outline-none text-sm py-2"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim()}
              className="w-10 h-10 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-full flex items-center justify-center hover:shadow-lg transition-all disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function formatText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
