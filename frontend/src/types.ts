export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  /** Stock by size (included by GET /api/products since Problem 9). */
  inventory: SizeStock[]
  total_stock: number
}

export type ProductDetail = Product

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/** Fields every product card needs. Both catalogue products and chat results satisfy this. */
export interface CardProduct {
  product_id: string
  name: string
  garment_type: string
  description: string
  image_url: string
  price: number
}

/** Product card returned with an agent reply (built from the database by the backend). */
export interface ChatProduct extends CardProduct {
  colors: string[]
  inventory: SizeStock[]
  total_stock: number
  reason: string
}

/** The API contract for chat results: what the page renders as product cards. */
export interface ChatResults {
  title: string
  total_matches: number
  products: ChatProduct[]
}

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
  created_at: string
}

/** Sent with every chat message so the agent knows what "this" / "the second one" means. */
export interface PageContext {
  path: string
  product_id: string | null
  listing_filter: string | null
  visible_product_ids: string[]
}

/** A saved chat message reloaded from the database (logged-in shoppers only). */
export interface SavedMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  results: ChatResults | null
  created_at: string
}

export interface ChatHistory {
  logged_in: boolean
  messages: SavedMessage[]
}
