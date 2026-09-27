/** Small New Haven / Connecticut / New England doodles, drawn in code (inline SVG). */

interface IconProps {
  size?: number
  className?: string
}

/** A New Haven "apizza" slice — thin crust with the famous charred spots. */
export function PizzaSlice({ size = 40, className }: IconProps) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 64 64" aria-hidden xmlns="http://www.w3.org/2000/svg">
      <path d="M8 14 C24 6 40 6 56 14 L33 60 Z" fill="#f4d27a" stroke="#c98f3c" strokeWidth="2" strokeLinejoin="round" />
      <path d="M8 14 C24 6 40 6 56 14 L54 19 C39 12 25 12 10 19 Z" fill="#c98f3c" />
      <circle cx="28" cy="25" r="4.5" fill="#c8453b" />
      <circle cx="40" cy="30" r="4" fill="#c8453b" />
      <circle cx="32" cy="41" r="3.5" fill="#c8453b" />
      <circle cx="21" cy="16" r="1.6" fill="#3b2a22" />
      <circle cx="44" cy="15" r="1.8" fill="#3b2a22" />
      <circle cx="35" cy="13" r="1.2" fill="#3b2a22" />
    </svg>
  )
}

/** A New England fall maple leaf. */
export function MapleLeaf({ size = 40, className, color = '#c9772b' }: IconProps & { color?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 64 64" aria-hidden xmlns="http://www.w3.org/2000/svg">
      <path
        d="M32 4 L37 16 L46 12 L44 24 L56 22 L50 32 L58 38 L44 40 L46 50 L34 44 L33 60 L31 60 L30 44 L18 50 L20 40 L6 38 L14 32 L8 22 L20 24 L18 12 L27 16 Z"
        fill={color}
        stroke="#8a4b1c"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path d="M32 18 L32 58" stroke="#8a4b1c" strokeWidth="1.2" />
    </svg>
  )
}

/** A Long Island Sound sailboat. */
export function Sailboat({ size = 40, className }: IconProps) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 64 64" aria-hidden xmlns="http://www.w3.org/2000/svg">
      <path d="M31 8 L31 44 L10 44 Z" fill="#ffffff" stroke="#0b2a4f" strokeWidth="2" strokeLinejoin="round" />
      <path d="M35 14 L35 44 L52 44 Z" fill="#a9c7e8" stroke="#0b2a4f" strokeWidth="2" strokeLinejoin="round" />
      <path d="M8 47 L56 47 L50 54 L14 54 Z" fill="#0b2a4f" />
      <path d="M4 59 C10 55 16 55 22 59 C28 63 34 63 40 59 C46 55 52 55 60 59" stroke="#6f9fd4" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  )
}

/** Soft coastal wave divider (full width). */
export function WaveDivider({ className, color = '#0b2a4f' }: { className?: string; color?: string }) {
  return (
    <svg className={className} viewBox="0 0 1440 60" preserveAspectRatio="none" aria-hidden xmlns="http://www.w3.org/2000/svg">
      <path d="M0 30 C180 60 360 0 540 25 C720 50 900 5 1080 25 C1260 45 1350 20 1440 28 L1440 60 L0 60 Z" fill={color} />
    </svg>
  )
}
