import { Link } from 'react-router-dom'
import HandsomeDan from './HandsomeDan'
import { MapleLeaf, PizzaSlice, Sailboat, WaveDivider } from './NewHavenIcons'

export default function Footer() {
  return (
    <footer className="footer">
      <WaveDivider className="footer-wave" />
      <div className="footer-body">
        <div className="footer-cols">
          <div className="footer-brand">
            <HandsomeDan variant="face" size={64} />
            <div>
              <h4>Campus Customs</h4>
              <p>
                57 Broadway
                <br />
                New Haven, CT 06511
              </p>
            </div>
          </div>
          <div>
            <h4>Shop</h4>
            <Link to="/products">All products</Link>
            <Link to="/products?type=hood">Hoodies</Link>
            <Link to="/products?type=crewneck">Crewnecks</Link>
            <Link to="/products?type=t-shirt">T-shirts</Link>
          </div>
          <div>
            <h4>Account</h4>
            <Link to="/login">Login</Link>
            <Link to="/create-account">Create account</Link>
            <Link to="/about">About us</Link>
          </div>
        </div>
        <div className="footer-local" aria-hidden>
          <PizzaSlice size={22} />
          <MapleLeaf size={22} />
          <Sailboat size={22} />
          <span>Proudly New Haven, Connecticut</span>
        </div>
        <p className="footer-note">© {new Date().getFullYear()} Campus Customs · Class project demo, not the official store.</p>
      </div>
    </footer>
  )
}
