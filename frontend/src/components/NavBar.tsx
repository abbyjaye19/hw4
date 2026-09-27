import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import HandsomeDan from './HandsomeDan'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About us' },
]

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="brand-mark">
          <HandsomeDan variant="face" size={38} title="Campus Customs home" />
        </span>
        <span className="brand-text">
          <strong>Campus Customs</strong>
          <small>Yale Bulldog Blue</small>
        </span>
      </Link>
      <nav className="nav-links">
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="nav-account">
        {loading ? null : user ? (
          <>
            <span className="nav-greeting">Hi, {user.first_name}!</span>
            <button className="btn btn-small btn-ghost" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login">Login</NavLink>
            <NavLink to="/create-account" className="btn btn-small">
              Create account
            </NavLink>
          </>
        )}
      </div>
    </header>
  )
}
