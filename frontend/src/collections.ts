// Store collections (mirroring yalebulldogblue.com's menu). Catalogue tags are
// inconsistent, so each collection is a list of keywords matched against product names.
export interface Collection {
  slug: string
  title: string
  blurb: string
  keywords: string[]
}

export const COLLECTIONS: Collection[] = [
  {
    slug: 'residential-colleges',
    title: 'Residential Colleges',
    blurb: 'Rep your college, from Pierson to Grace Hopper.',
    keywords: [
      'benjamin franklin', 'berkeley', 'branford', 'davenport', 'ezra stiles', 'grace hopper', 'jonathan edwards',
      'morse', 'pauli murray', 'pierson', 'saybrook', 'silliman', 'timothy dwight', 'trumbull',
    ],
  },
  {
    slug: 'sports',
    title: 'Sports',
    blurb: 'Hockey, crew, squash, sailing and more.',
    keywords: ['left chest', 'sports', 'diving t-shirt'],
  },
  {
    slug: 'relatives',
    title: 'Relatives',
    blurb: 'For Yale moms, dads, grandparents, aunts and uncles.',
    keywords: ['yale mom', 'yale dad', 'grandma', 'grandpa', 'yale aunt', 'yale uncle', 'yale brother', 'yale cousin'],
  },
  {
    slug: 'grad-schools',
    title: 'Graduate & Professional Schools',
    blurb: 'Law, Medicine, Art, Music, Management and more.',
    keywords: ['school of', 'law school', 'divinity school', 'forest school'],
  },
]

export function inCollection(productName: string, collection: Collection): boolean {
  const name = productName.toLowerCase()
  return collection.keywords.some((k) => name.includes(k))
}
