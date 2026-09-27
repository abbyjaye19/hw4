import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api'
import { typeCrumb, type FromState } from '../navigation'
import type { ProductDetail } from '../types'

const LOW_STOCK = 5

export default function ProductPage() {
  const { productId = '' } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const came = location.state as FromState | null
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState('')
  const [selectedSize, setSelectedSize] = useState('')

  useEffect(() => {
    setProduct(null)
    setError('')
    setSelectedSize('')
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError('We could not find that product.'))
  }, [productId])

  if (error) {
    return (
      <div className="page">
        <p className="error">{error}</p>
        <Link to="/products">← Back to all products</Link>
      </div>
    )
  }
  if (!product) return <div className="page muted">Loading…</div>

  const selected = product.inventory.find((i) => i.size === selectedSize)

  // Breadcrumb middle step: where the shopper came from, or the item's category if they arrived directly.
  const cameFromListing = came && (came.from.startsWith('/products?') || came.from === '/products')
  const middle = cameFromListing ? { label: came.fromLabel, to: came.from } : typeCrumb(product.garment_type, product.name)

  function goBack() {
    if (came) navigate(came.from, { state: { restoreScroll: true } })
    else navigate('/products')
  }

  return (
    <div className="page">
      <div className="product-nav">
        <button className="back-button" onClick={goBack}>
          ← Back to {came ? came.fromLabel : 'all products'}
        </button>
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link>
          <span aria-hidden>›</span>
          <Link to="/products">Products</Link>
          {middle && middle.label !== 'All products' && (
            <>
              <span aria-hidden>›</span>
              <Link to={middle.to} state={{ restoreScroll: true }}>
                {middle.label}
              </Link>
            </>
          )}
          <span aria-hidden>›</span>
          <span aria-current="page">{product.name}</span>
        </nav>
      </div>
      <div className="product-detail">
        <div className="product-detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <span className="eyebrow">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="price price-large">{formatPrice(product.price)}</p>
          <p className="description">{product.description}</p>

          <h4>Colors</h4>
          <div className="chips">
            {product.colors.map((c) => (
              <span key={c} className="chip">
                {c}
              </span>
            ))}
          </div>

          <h4>Sizes &amp; stock</h4>
          <div className="sizes">
            {product.inventory.map((s) => (
              <button
                key={s.size}
                className={`size ${selectedSize === s.size ? 'active' : ''}`}
                disabled={s.quantity === 0}
                onClick={() => setSelectedSize(s.size)}
                title={s.quantity === 0 ? 'Out of stock' : `${s.quantity} in stock`}
              >
                <strong>{s.size}</strong>
                <small>{s.quantity === 0 ? 'Sold out' : `${s.quantity} left`}</small>
              </button>
            ))}
          </div>
          <p className="stock-note">
            {selected
              ? selected.quantity <= LOW_STOCK
                ? `Only ${selected.quantity} left in ${selected.size} — grab it soon!`
                : `${selected.quantity} in stock in ${selected.size}.`
              : product.total_stock > 0
                ? `${product.total_stock} in stock across all sizes. Pick a size to check availability.`
                : 'Currently sold out in every size.'}
          </p>

          <h4>Tags</h4>
          <div className="chips">
            {product.search_tags.map((t) => (
              <span key={t} className="chip chip-muted">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
