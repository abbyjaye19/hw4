import { useEffect } from 'react'
import { useLocation, useNavigationType } from 'react-router-dom'

const key = (path: string) => `scroll:${path}`

/**
 * Back-navigation helper (Problem 9):
 * - remembers the scroll position of every page (path + filters) in sessionStorage;
 * - going Back (browser button or our "Back to results" button) returns to that exact spot;
 * - any other navigation starts at the top of the new page.
 */
export default function ScrollManager() {
  const location = useLocation()
  const navType = useNavigationType()
  const path = location.pathname + location.search
  const restore = navType === 'POP' || (location.state as { restoreScroll?: boolean } | null)?.restoreScroll

  // Save the scroll position of the current page while the shopper scrolls.
  useEffect(() => {
    const onScroll = () => {
      // After a click the URL changes before this listener is removed, and the shorter new page
      // fires a scroll event; ignore it so it can't overwrite the list's saved position.
      if (window.location.pathname + window.location.search !== path) return
      sessionStorage.setItem(key(path), String(Math.round(window.scrollY)))
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [path])

  // On arrival: restore the saved spot when going back, otherwise jump to the top.
  useEffect(() => {
    if (!restore) {
      window.scrollTo(0, 0)
      return
    }
    const target = Number(sessionStorage.getItem(key(path)) ?? 0)
    // Product grids load asynchronously, so retry until the page is tall enough (max ~1.5s).
    let tries = 0
    const timer = window.setInterval(() => {
      tries += 1
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight
      if (maxScroll >= target || tries > 30) {
        window.scrollTo(0, target)
        window.clearInterval(timer)
      }
    }, 50)
    return () => window.clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.key])

  return null
}
