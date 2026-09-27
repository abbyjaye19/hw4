import type { ChatHistory, ChatMessage, ChatResults, PageContext, Product, ProductDetail, User } from './types'

// Requests go to /api/*; Vite proxies them to FastAPI on port 8000.
async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export function fetchProducts(q?: string): Promise<Product[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : ''
  return getJson<Product[]>(`/api/products${query}`)
}

export function fetchProduct(productId: string): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)
}

// ---------- Auth ----------
// The session lives in an HttpOnly cookie set by the backend, so JavaScript never touches the token.

async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      // FastAPI validation errors: [{ loc: [..., 'field'], msg }]
      return body.detail
        .map((d: { loc?: string[]; msg: string }) => `${d.loc?.at(-1)?.replace('_', ' ') ?? 'field'}: ${d.msg}`)
        .join('. ')
    }
  } catch {
    /* fall through */
  }
  return `Something went wrong (${res.status}).`
}

async function postJson<T>(url: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await readError(res))
  return (res.status === 204 ? undefined : await res.json()) as T
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
}

export function register(input: RegisterInput): Promise<User> {
  return postJson<User>('/api/auth/register', input)
}

export function login(email: string, password: string): Promise<User> {
  return postJson<User>('/api/auth/login', { email, password })
}

export function logout(): Promise<void> {
  return postJson<void>('/api/auth/logout')
}

export async function fetchCurrentUser(): Promise<User | null> {
  const res = await fetch('/api/auth/me', { credentials: 'include' })
  return res.ok ? ((await res.json()) as User | null) : null
}

// ---------- Chat ----------
/** POST /api/chat response: the chat text plus (optionally) product matches to render as cards. */
export interface ChatReply {
  reply: string
  results: ChatResults | null
  /** 'timeout' / 'too_complex' = the agent hit its thinking time or step limit (Problem 9). */
  status: 'ok' | 'timeout' | 'too_complex' | 'unverified'
  seconds: number | null
}

// Sends the new message, earlier turns (used for guests), and the current page context to the agent.
// The session cookie goes along: for logged-in shoppers the server loads/saves history in the database.
export function sendChatMessage(
  message: string,
  history: ChatMessage[],
  page: PageContext,
  signal?: AbortSignal,
): Promise<ChatReply> {
  return postJson<ChatReply>('/api/chat', { message, history, page }, signal)
}

export async function fetchChatHistory(): Promise<ChatHistory> {
  const res = await fetch('/api/chat/history', { credentials: 'include' })
  if (!res.ok) return { logged_in: false, messages: [] }
  return (await res.json()) as ChatHistory
}

export function formatPrice(price: number): string {
  return price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}
