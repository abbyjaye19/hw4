import { Link } from 'react-router-dom'

export default function About() {
  return (
    <div className="page page-narrow">
      <div className="page-head">
        <span className="eyebrow">About us</span>
        <h1>Yale spirit, with a creative twist</h1>
        <p>Campus Customs is a Yale clothing and accessories store with a little extra personality stitched in.</p>
      </div>

      <section className="prose">
        <h2>What is Campus Customs?</h2>
        <p>
          We're the New Haven shop where Bulldog pride meets fresh design. Sure, you'll find the classic navy hoodie
          (Handsome Dan would never forgive us if you didn't). You'll also find vintage bulldogs in sailor hats, crests
          for every residential college, and a "Yale Grandpa" crewneck made for bragging at family dinners.
        </p>

        <h2>Our twist</h2>
        <p>
          Anyone can print "YALE" on a sweatshirt. We like to ask what makes <em>your</em> Yale yours: your college,
          your team, your school, or the family member who has been waiting four years to wear the shirt. Then we make
          gear that says it.
        </p>
        <ul>
          <li>
            <strong>Residential colleges:</strong> show your college colors, from Pierson to Grace Hopper.
          </li>
          <li>
            <strong>Sports:</strong> hockey, crew, squash, sailing, fencing and more, for players and fans in the stands.
          </li>
          <li>
            <strong>Grad &amp; professional schools:</strong> Law, Medicine, Art, Music, Management and beyond.
          </li>
          <li>
            <strong>Relatives:</strong> Yale Mom, Dad, Grandma, Grandpa, Aunt, Uncle, Brother and Cousin.
          </li>
        </ul>

        <h2>Straight talk, always</h2>
        <p>
          Our chat assistant checks the shop's real inventory, so when it tells you a price or says a size is in stock,
          it's true. If we're sold out of your size, we'll tell you (and point you to something just as good).
        </p>

        <h2>Come say hi</h2>
        <p>
          57 Broadway
          <br />
          New Haven, CT 06511
        </p>
        <p>
          Boola Boola! <Link to="/products">Start shopping →</Link>
        </p>
      </section>
    </div>
  )
}
