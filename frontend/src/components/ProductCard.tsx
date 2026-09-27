import { Link, useLocation } from 'react-router-dom'
import { formatPrice } from '../api'
import { labelForPage, type FromState } from '../navigation'
import type { CardProduct, SizeStock } from '../types'

function shortText(text: string, max = 90): string {
  return text.length <= max ? text : text.slice(0, text.lastIndexOf(' ', max)) + '…'
}

interface Props {
  product: CardProduct & { reason?: string; inventory?: SizeStock[] }
  /** Overrides the "Back to …" label on the product page (e.g. chat results). */
  fromLabel?: string
  /** When the shopper filtered by a size, show stock for that size on the card. */
  highlightSize?: string
}

/**
 * The one product card used everywhere (Products page, Home, and chat results).
 * Clicking it always opens the single-item page at /products/:productId, and remembers
 * where the shopper came from so the product page can offer "Back to …".
 */
export default function ProductCard({ product, fromLabel, highlightSize }: Props) {
  const location = useLocation()
  const state: FromState = {
    from: location.pathname + location.search,
    fromLabel: fromLabel ?? labelForPage(location.pathname, location.search),
  }
  const inStock = product.inventory?.filter((s) => s.quantity > 0).map((s) => s.size)
  const sizeQty = highlightSize ? product.inventory?.find((s) => s.size === highlightSize)?.quantity : undefined

  let stockLine: { text: string; cls: string } | null = null
  if (sizeQty !== undefined) {
    stockLine = { text: `${sizeQty} left in ${highlightSize}`, cls: sizeQty <= 5 ? 'low' : 'muted' }
  } else if (inStock) {
    stockLine = inStock.length ? { text: `In stock: ${inStock.join(' · ')}`, cls: 'muted' } : { text: 'Sold out', cls: 'error' }
  }

  return (
    <Link to={`/products/${product.product_id}`} state={state} className="product-card">
      <div className="product-card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {inStock && inStock.length === 0 && <span className="badge badge-soldout">Sold out</span>}
      </div>
      <div className="product-card-body">
        <span className="eyebrow">{product.garment_type}</span>
        <h3>{product.name}</h3>
        {product.reason && <p className="card-reason">{product.reason}</p>}
        <p>{shortText(product.description)}</p>
        <div className="card-foot">
          <strong className="price">{formatPrice(product.price)}</strong>
          {stockLine && <small className={stockLine.cls}>{stockLine.text}</small>}
        </div>
      </div>
    </Link>
  )
}
