import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ChatResults } from './types'

// The latest product matches from the chat agent, shared so the page can render them as cards.
interface ChatMatchesState {
  results: ChatResults | null
  /** Bumps every time new results arrive, so the panel can scroll into view / re-open. */
  version: number
  showResults: (results: ChatResults) => void
  clearResults: () => void
}

const ChatMatchesContext = createContext<ChatMatchesState | null>(null)

export function ChatMatchesProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  const [version, setVersion] = useState(0)

  const showResults = (r: ChatResults) => {
    setResults(r)
    setVersion((v) => v + 1)
  }
  const clearResults = () => setResults(null)

  return (
    <ChatMatchesContext.Provider value={{ results, version, showResults, clearResults }}>
      {children}
    </ChatMatchesContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChatMatches(): ChatMatchesState {
  const ctx = useContext(ChatMatchesContext)
  if (!ctx) throw new Error('useChatMatches must be used inside <ChatMatchesProvider>')
  return ctx
}
