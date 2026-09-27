import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import { COLLECTIONS, inCollection } from '../collections'
import type { Product } from '../types'

const CATEGORIES = [
  { label: 'All', match: '' },
  { label: 'Hoodies', match: 'hood' },
  { label: 'Crewnecks', match: 'crewneck' },
  { label: 'T-shirts', match: 't-shirt' },
  { label: 'Quarter-zips', match: 'quarter-zip' },
  { label: 'Jackets & Fleece', match: 'jacket' },
]

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

const SORTS = [
  { value: '', label: 'Name (A–Z)' },
  { value: 'price-asc', label: 'Price: low to high' },
  { value: 'price-desc', label: 'Price: high to low' },
  { value: 'stock', label: 'Most in stock' },
]

function qtyIn(p: Product, size: string): number {
  return p.inventory.find((s) => s.size === size)?.quantity ?? 0
}

function matches(p: Product, term: string): boolean {
  const haystack = [p.name, p.garment_type, p.description, ...p.colors, ...p.search_tags].join(' ').toLowerCase()
  return haystack.includes(term.toLowerCase())
}

export default function Products() {
  const [params, setParams] = useSearchParams()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const search = params.get('q') ?? ''
  const category = params.get('type') ?? ''
  const collection = COLLECTIONS.find((c) => c.slug === params.get('collection'))
  const size = SIZES.includes(params.get('size') ?? '') ? params.get('size')! : ''
  const sort = params.get('sort') ?? ''

  // Filters live in the URL, so "Back to results" and the browser Back button return to the same view.
  // Functional update: quick successive clicks (category → size → sort) build on each other
  // instead of overwriting one another.
  function setParam(name: string, value: string) {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (value) next.set(name, value)
        else next.delete(name)
        return next
      },
      { replace: true },
    )
  }

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError('Could not load products. Is the backend running on port 8000?'))
      .finally(() => setLoading(false))
  }, [])

  // Category / search / collection first (so we can say how many are hidden by the size filter).
  const matching = useMemo(
    () =>
      products.filter(
        (p) =>
          (!category || p.garment_type.toLowerCase().includes(category)) &&
          (!search || matches(p, search)) &&
          (!collection || inCollection(p.name, collection)),
      ),
    [products, category, search, collection],
  )

  const visible = useMemo(() => {
    const list = size ? matching.filter((p) => qtyIn(p, size) > 0) : [...matching]
    const byName = (a: Product, b: Product) => a.name.localeCompare(b.name)
    if (sort === 'price-asc') list.sort((a, b) => a.price - b.price || byName(a, b))
    else if (sort === 'price-desc') list.sort((a, b) => b.price - a.price || byName(a, b))
    else if (sort === 'stock')
      list.sort((a, b) => (size ? qtyIn(b, size) - qtyIn(a, size) : b.total_stock - a.total_stock) || byName(a, b))
    else list.sort(byName)
    return list
  }, [matching, size, sort])

  const hiddenBySize = matching.length - visible.length
  const anyFilter = Boolean(category || search || collection || size || sort)

  return (
    <div className="page">
      <div className="page-head">
        <h1>{collection ? collection.title : 'Shop Bulldog Blue'}</h1>
        <p>
          {collection
            ? collection.blurb
            : 'Hoodies, crewnecks, tees and layers for students, alumni and every proud Yale relative.'}
          {collection && (
            <>
              {' '}
              <button className="link-button" onClick={() => setParams({}, { replace: true })}>
                Show all products
              </button>
            </>
          )}
        </p>
      </div>

      <div className="filters">
        <div className="pills">
          {CATEGORIES.map((c) => (
            <button
              key={c.label}
              className={`pill ${category === c.match ? 'active' : ''}`}
              onClick={() => setParam('type', c.match)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <input
          className="search"
          type="search"
          placeholder="Search e.g. hockey, Pierson, mom, gray…"
          value={search}
          onChange={(e) => setParam('q', e.target.value)}
        />
      </div>

      <div className="filters filters-secondary">
        <div className="size-filter" role="group" aria-label="Only show items in stock in size">
          <span className="filter-label">In stock in my size:</span>
          <button className={`size-chip ${size === '' ? 'active' : ''}`} onClick={() => setParam('size', '')}>
            Any
          </button>
          {SIZES.map((sz) => (
            <button
              key={sz}
              className={`size-chip ${size === sz ? 'active' : ''}`}
              onClick={() => setParam('size', size === sz ? '' : sz)}
              aria-pressed={size === sz}
            >
              {sz}
            </button>
          ))}
        </div>
        <label className="sort">
          <span className="filter-label">Sort by</span>
          <select value={sort} onChange={(e) => setParam('sort', e.target.value)}>
            {SORTS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <p className="muted">Loading products…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <>
          <p className="result-count">
            <strong>{visible.length}</strong> {visible.length === 1 ? 'item' : 'items'}
            {size && ` in stock in ${size}`}
            {size && hiddenBySize > 0 && <span className="muted"> · {hiddenBySize} more sold out in {size}</span>}
            {anyFilter && (
              <button className="link-button clear-filters" onClick={() => setParams({}, { replace: true })}>
                Clear all filters
              </button>
            )}
          </p>
          <div className="product-grid">
            {visible.map((p) => (
              <ProductCard key={p.product_id} product={p} highlightSize={size || undefined} />
            ))}
          </div>
          {visible.length === 0 && (
            <p className="muted">
              {size && matching.length > 0
                ? `Everything that matches is sold out in ${size}. Try another size, or ask the chat for alternatives.`
                : 'No products match that search.'}
            </p>
          )}
        </>
      )}
    </div>
  )
}
