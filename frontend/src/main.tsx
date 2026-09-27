import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import './theme.css'
import App from './App.tsx'
import { AuthProvider } from './auth.tsx'
import { ChatMatchesProvider } from './chatMatches.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ChatMatchesProvider>
          <App />
        </ChatMatchesProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
