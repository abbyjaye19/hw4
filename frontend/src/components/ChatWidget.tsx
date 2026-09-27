import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { fetchChatHistory, formatPrice, sendChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatMatches } from '../chatMatches'
import type { ChatMessage, ChatResults, PageContext } from '../types'
import HandsomeDan from './HandsomeDan'

interface WidgetMessage extends ChatMessage {
  results?: ChatResults | null
  /** Greeting / divider / notice shown only in the widget, never sent to the agent. */
  local?: 'greeting' | 'divider' | 'notice'
}

// Thinking time limit (Problem 9): the server stops the agent at 25s; the browser gives up at 35s
// as a backup (e.g. network trouble), and the shopper can cancel at any time.
const CLIENT_TIMEOUT_MS = 35_000
const SLOW_AFTER_S = 6

const CHAT_PREVIEW_CARDS = 4

function greeting(firstName?: string, returning = false): WidgetMessage {
  return {
    role: 'assistant',
    local: 'greeting',
    content: returning
      ? `Welcome back, ${firstName}! Here's our earlier chat. What can I help you find today?`
      : `Hi${firstName ? ` ${firstName}` : ''}, I'm the Campus Customs assistant! Ask me about hoodies, sizes, prices or what's in stock.`,
  }
}

/** Where the shopper is right now, so "this" / "the second one" can be resolved by the agent. */
function usePageContext(): PageContext {
  const { pathname } = useLocation()
  const [params] = useSearchParams()
  const { results } = useChatMatches()
  const detail = pathname.match(/^\/products\/([^/]+)$/)
  const filter = pathname === '/products' ? params.toString() || null : null
  return {
    path: pathname,
    product_id: detail ? decodeURIComponent(detail[1]) : null,
    listing_filter: filter,
    visible_product_ids: results?.products.map((p) => p.product_id) ?? [],
  }
}

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const { showResults, clearResults } = useChatMatches()
  const page = usePageContext()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<WidgetMessage[]>([greeting()])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const abortRef = useRef<AbortController | null>(null)
  const cancelledRef = useRef(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Seconds counter while the assistant is thinking.
  useEffect(() => {
    if (!thinking) return
    setElapsed(0)
    const started = Date.now()
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 500)
    return () => window.clearInterval(timer)
  }, [thinking])

  function cancel() {
    cancelledRef.current = true
    abortRef.current?.abort()
  }

  // When the shopper changes (page load, login, logout): guests start fresh,
  // logged-in shoppers get their saved conversation reloaded from the database.
  useEffect(() => {
    if (loading) return
    let cancelled = false
    clearResults()
    setMessages([greeting(user?.first_name)])
    if (user) {
      fetchChatHistory().then(({ messages: saved }) => {
        if (cancelled || saved.length === 0) return
        setMessages([
          ...saved.map((m) => ({ role: m.role, content: m.content, results: m.results })),
          { role: 'assistant', content: 'Earlier conversation', local: 'divider' },
          greeting(user.first_name, true),
        ])
      })
    }
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user?.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking, open])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || thinking) return
    // Earlier turns give a guest's agent context for follow-ups. (Logged in: the server uses saved history.)
    const history: ChatMessage[] = messages.filter((m) => !m.local).map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setThinking(true)
    const controller = new AbortController()
    abortRef.current = controller
    cancelledRef.current = false
    const backupTimer = window.setTimeout(() => controller.abort(), CLIENT_TIMEOUT_MS)
    try {
      const { reply, results, status } = await sendChatMessage(text, history, page, controller.signal)
      // Replies that hit the time/step limit are shown as a notice (and aren't saved or sent back to the agent).
      setMessages((m) => [...m, { role: 'assistant', content: reply, results, local: status === 'ok' ? undefined : 'notice' }])
      // Contract: when the agent returns product matches, render them as cards on the page.
      if (results && results.products.length) showResults(results)
    } catch (err) {
      const aborted = err instanceof DOMException && err.name === 'AbortError'
      const msg = aborted
        ? cancelledRef.current
          ? 'Okay, I stopped looking. Ask me something else anytime!'
          : "Sorry, that took too long and I stopped waiting. Please try again, maybe with a simpler question."
        : err instanceof Error
          ? err.message
          : 'Sorry, I could not reach the shop right now. Please try again.'
      setMessages((m) => [...m, { role: 'assistant', content: msg, local: 'notice' }])
    } finally {
      window.clearTimeout(backupTimer)
      abortRef.current = null
      setThinking(false)
    }
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Shopping assistant chat">
          <header className="chat-header">
            <div className="chat-title">
              <span className="chat-avatar">
                <HandsomeDan variant="face" size={30} title="" />
              </span>
              <div>
                <strong>Campus Customs Concierge</strong>
                <small>Live prices &amp; stock from our shop floor</small>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-messages">
            {messages.map((m, i) =>
              m.local === 'divider' ? (
                <div key={i} className="chat-divider">
                  <span>Earlier conversation above</span>
                </div>
              ) : (
              <div key={i} className={`bubble-group bubble-group-${m.role}`}>
                <div className={`bubble bubble-${m.role} ${m.local === 'notice' ? 'bubble-notice' : ''}`}>{m.content}</div>
                {m.results && m.results.products.length > 0 && (
                  <>
                    <div className="chat-cards">
                      {m.results.products.slice(0, CHAT_PREVIEW_CARDS).map((p) => (
                        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-card">
                          <img src={p.image_url} alt={p.name} />
                          <span>{p.name}</span>
                          <strong>{formatPrice(p.price)}</strong>
                        </Link>
                      ))}
                    </div>
                    <button className="link-button small" onClick={() => m.results && showResults(m.results)}>
                      {m.results.products.length > CHAT_PREVIEW_CARDS
                        ? `See all ${m.results.products.length} on the page ↑`
                        : 'Show on the page ↑'}
                    </button>
                  </>
                )}
              </div>
              ),
            )}
            {thinking && (
              <div className="thinking-row">
                <div className="bubble bubble-assistant thinking" aria-label="Assistant is thinking">
                  <span />
                  <span />
                  <span />
                </div>
                {elapsed >= SLOW_AFTER_S && <span className="thinking-status">Still checking the stockroom… {elapsed}s</span>}
                <button type="button" className="cancel-button" onClick={cancel}>
                  Cancel
                </button>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message and press Enter…"
              aria-label="Chat message"
              maxLength={1000}
              autoFocus
            />
            <button type="submit" className="btn" disabled={thinking || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        className={`chat-toggle ${open ? 'is-open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open shopping assistant chat'}
      >
        {open ? (
          <span className="chat-toggle-close">×</span>
        ) : (
          <>
            <span className="chat-avatar">
              <HandsomeDan variant="face" size={30} title="" />
            </span>
            <span className="chat-toggle-label">
              <strong>Ask Dan</strong>
              <small>Sizes, prices &amp; stock</small>
            </span>
          </>
        )}
      </button>
    </div>
  )
}
