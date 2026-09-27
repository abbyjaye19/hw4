import { Link } from 'react-router-dom'
import HandsomeDan from '../components/HandsomeDan'

export default function NotFound() {
  return (
    <div className="page page-narrow not-found">
      <HandsomeDan size={140} />
      <h1>Page not found</h1>
      <p>
        That page wandered off campus. <Link to="/">Head home</Link> or <Link to="/products">browse products</Link>.
      </p>
    </div>
  )
}
