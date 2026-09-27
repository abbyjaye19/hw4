import { COLLECTIONS } from './collections'

/** Remembered on every product-card click so the product page can offer "Back to …". */
export interface FromState {
  from: string // path + search the shopper came from, e.g. "/products?type=hood&size=M"
  fromLabel: string // human label, e.g. "Hoodies"
}

const TYPE_LABELS: Record<string, string> = {
  hood: 'Hoodies',
  crewneck: 'Crewnecks',
  't-shirt': 'T-shirts',
  'quarter-zip': 'Quarter-zips',
  jacket: 'Jackets & Fleece',
}

/** A friendly name for a page the shopper can go back to. */
export function labelForPage(pathname: string, search: string): string {
  const params = new URLSearchParams(search)
  if (pathname === '/products') {
    const collection = COLLECTIONS.find((c) => c.slug === params.get('collection'))
    const type = params.get('type')
    const q = params.get('q')
    if (collection) return collection.title
    if (type && TYPE_LABELS[type]) return TYPE_LABELS[type]
    if (q) return `Search: “${q}”`
    return 'All products'
  }
  if (pathname === '/') return 'Home'
  if (pathname === '/about') return 'About us'
  if (pathname.startsWith('/products/')) return 'previous item'
  return 'previous page'
}

/** Garment family for a breadcrumb when the shopper arrived directly (no "from" state). */
export function typeCrumb(garmentType: string, name: string): { label: string; to: string } | null {
  const text = `${garmentType} ${name}`.toLowerCase()
  const match = Object.keys(TYPE_LABELS).find((k) => text.includes(k) || (k === 'quarter-zip' && text.includes('1 4 zip')))
  return match ? { label: TYPE_LABELS[match], to: `/products?type=${encodeURIComponent(match)}` } : null
}
