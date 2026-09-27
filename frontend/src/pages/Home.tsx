import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts } from '../api'
import HandsomeDan from '../components/HandsomeDan'
import { MapleLeaf, PizzaSlice, Sailboat } from '../components/NewHavenIcons'
import ProductCard from '../components/ProductCard'
import { COLLECTIONS } from '../collections'
import type { Product } from '../types'

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  'district-vit-crewneck-vintage-bulldog',
  '2025-yale-vs-harvard-t-shirt',
  'brooks-brothers-bomber-jacket-yale',
]

const QUICK_SHOP = [
  { label: 'Hoodies', type: 'hood' },
  { label: 'Crewnecks', type: 'crewneck' },
  { label: 'T-shirts', type: 't-shirt' },
  { label: 'Quarter-zips', type: 'quarter-zip' },
  { label: 'Jackets', type: 'jacket' },
]

// Little odes to New Haven & New England, each leading somewhere useful in the shop.
const LOCAL_NOTES = [
  {
    icon: <PizzaSlice size={44} />,
    title: 'Apizza-approved comfort',
    text: 'Soft hoodies for the line at Pepe’s on Wooster Street.',
    to: '/products?type=hood',
  },
  {
    icon: <MapleLeaf size={44} />,
    title: 'Fall on the Green',
    text: 'Quarter-zips and crewnecks for crisp New England afternoons.',
    to: '/products?type=quarter-zip',
  },
  {
    icon: <Sailboat size={44} />,
    title: 'Shoreline layers',
    text: 'Fleece and jackets for breezy days on Long Island Sound.',
    to: '/products?type=jacket',
  },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => setFeatured(FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter((p): p is Product => !!p)))
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <span className="eyebrow eyebrow-metal">Boola Boola · Go Bulldogs</span>
            <h1>
              Handsome Dan’s <em>favorite</em> clothing store
            </h1>
            <p>Yale gear for students, alumni, and every proud Bulldog fan. Made for New Haven winters, game days and everything in between.</p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-metal">
                Shop the collection
              </Link>
              <Link to="/products?type=hood" className="btn btn-outline">
                Hoodies
              </Link>
            </div>
          </div>
          <div className="hero-art" aria-hidden>
            <div className="hero-medallion">
              <HandsomeDan size={230} />
            </div>
            <MapleLeaf className="float leaf-1" size={34} />
            <MapleLeaf className="float leaf-2" size={26} color="#d4a24c" />
            <PizzaSlice className="float pizza-1" size={40} />
          </div>
        </div>
      </section>

      <div className="page">
        <section>
          <h2 className="section-title">What are you looking for?</h2>
          <div className="quick-shop">
            {QUICK_SHOP.map((q) => (
              <Link key={q.type} to={`/products?type=${encodeURIComponent(q.type)}`} className="quick-shop-link">
                {q.label}
              </Link>
            ))}
          </div>
        </section>

        <section>
          <div className="section-head">
            <h2>Dan’s picks</h2>
            <Link to="/products">See everything →</Link>
          </div>
          <div className="product-grid">
            {featured.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>

        <section className="local-notes" aria-label="New Haven favorites">
          {LOCAL_NOTES.map((n) => (
            <Link key={n.title} to={n.to} className="local-note">
              <span className="local-icon">{n.icon}</span>
              <span>
                <strong>{n.title}</strong>
                <small>{n.text}</small>
              </span>
            </Link>
          ))}
        </section>

        <section>
          <h2 className="section-title">Shop by collection</h2>
          <div className="collections">
            {COLLECTIONS.map((c) => (
              <Link key={c.slug} to={`/products?collection=${c.slug}`} className="collection">
                <h3>{c.title}</h3>
                <p>{c.blurb}</p>
                <span>Shop →</span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </>
  )
}
