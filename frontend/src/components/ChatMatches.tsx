import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useChatMatches } from '../chatMatches'
import ProductCard from './ProductCard'

/**
 * Chat results panel: renders the agent's product matches as regular product cards
 * at the top of the page. Each card opens the single-item page, like everywhere else.
 * On a single-item page the panel collapses to a slim bar so the product stays in view.
 */
export default function ChatMatches() {
  const { results, version, clearResults } = useChatMatches()
  const { pathname } = useLocation()
  const onDetailPage = /^\/products\/[^/]+$/.test(pathname)
  const [expanded, setExpanded] = useState(true)
  const ref = useRef<HTMLElement>(null)

  // New results from the chat: open the panel and bring it into view.
  useEffect(() => {
    if (version === 0) return
    setExpanded(true)
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [version])

  // Opening a card collapses the panel so the detail view is front and center.
  useEffect(() => {
    if (onDetailPage) setExpanded(false)
  }, [pathname, onDetailPage])

  if (!results) return null
  const { title, total_matches, products } = results
  const count =
    total_matches > products.length ? `Showing ${products.length} of ${total_matches}` : `${products.length} item${products.length === 1 ? '' : 's'}`

  return (
    <section ref={ref} className={`chat-results ${expanded ? '' : 'collapsed'}`} aria-label="Products from your chat">
      <div className="chat-results-head">
        <div>
          <span className="eyebrow">From your chat</span>
          <strong className="chat-results-title">{title}</strong>
          <span className="muted"> · {count}</span>
        </div>
        <div className="chat-results-actions">
          <button className="link-button" onClick={() => setExpanded((e) => !e)}>
            {expanded ? 'Collapse' : 'Show results'}
          </button>
          <button className="link-button" onClick={clearResults}>
            Clear
          </button>
        </div>
      </div>
      {expanded && (
        <div className="product-grid">
          {products.map((p) => (
            <ProductCard key={p.product_id} product={p} fromLabel={`chat results (${title})`} />
          ))}
        </div>
      )}
    </section>
  )
}
