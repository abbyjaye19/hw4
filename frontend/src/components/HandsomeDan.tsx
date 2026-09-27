import { useId } from 'react'

interface Props {
  /** Pixel width; height follows the drawing's aspect ratio. */
  size?: number
  /** Full = head + navy "Y" sweater (hero); face = head only (logo, chat). */
  variant?: 'full' | 'face'
  className?: string
  title?: string
}

/**
 * Handsome Dan, drawn in code (inline SVG, no image file): an English bulldog with
 * a brindle eye patch, underbite, and a silver-and-gold collar tag.
 */
export default function HandsomeDan({ size = 160, variant = 'full', className, title = 'Handsome Dan, the Yale bulldog' }: Props) {
  const id = useId().replace(/:/g, '')
  const full = variant === 'full'
  const viewBox = full ? '0 0 200 236' : '10 8 180 170'
  const height = full ? (size * 236) / 200 : (size * 170) / 180

  return (
    <svg
      className={className}
      width={size}
      height={height}
      viewBox={viewBox}
      role={title ? 'img' : undefined}
      aria-label={title || undefined}
      aria-hidden={title ? undefined : true}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id={`metal-${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#c4cad2" />
          <stop offset="35%" stopColor="#f4f6f8" />
          <stop offset="60%" stopColor="#d4af37" />
          <stop offset="100%" stopColor="#f5e3a1" />
        </linearGradient>
        <radialGradient id={`fur-${id}`} cx="50%" cy="40%" r="65%">
          <stop offset="0%" stopColor="#fbf8f3" />
          <stop offset="100%" stopColor="#e9e0d3" />
        </radialGradient>
      </defs>

      {full && (
        <g>
          {/* Navy sweater with a white collegiate Y */}
          <path d="M28 236 C30 190 58 168 100 168 C142 168 170 190 172 236 Z" fill="#0b2a4f" />
          <path d="M62 176 C76 184 124 184 138 176" stroke="#ffffff" strokeOpacity="0.35" strokeWidth="5" fill="none" />
          <text x="100" y="224" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="40" fill="#ffffff">
            Y
          </text>
        </g>
      )}

      {/* Ears (folded "rose" ears) */}
      <path d="M40 58 C30 40 44 24 62 34 C66 44 60 56 52 66 Z" fill="#b98f6a" />
      <path d="M160 58 C170 40 156 24 138 34 C134 44 140 56 148 66 Z" fill="#8a6446" />

      {/* Head */}
      <ellipse cx="100" cy="92" rx="72" ry="62" fill={`url(#fur-${id})`} stroke="#d9cdbd" strokeWidth="1.5" />
      {/* Brindle patch over his left eye */}
      <path d="M112 50 C142 44 160 62 158 88 C148 96 128 94 116 84 C108 74 106 60 112 50 Z" fill="#b08662" opacity="0.9" />
      {/* Brow wrinkles */}
      <path d="M72 58 C86 52 96 54 100 60" stroke="#cdbba5" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M76 68 C88 63 96 64 100 69" stroke="#cdbba5" strokeWidth="2.5" fill="none" strokeLinecap="round" />

      {/* Eyes */}
      <ellipse cx="74" cy="84" rx="10" ry="9" fill="#2a2320" />
      <ellipse cx="128" cy="84" rx="10" ry="9" fill="#2a2320" />
      <circle cx="77" cy="81" r="3" fill="#ffffff" />
      <circle cx="131" cy="81" r="3" fill="#ffffff" />

      {/* Muzzle + jowls */}
      <path d="M52 118 C52 96 76 92 100 96 C124 92 148 96 148 118 C148 142 128 152 100 150 C72 152 52 142 52 118 Z" fill="#fdfbf7" stroke="#e2d7c8" strokeWidth="1.5" />
      <path d="M100 112 L100 124" stroke="#6b5a4e" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M100 124 C90 134 74 132 66 124" stroke="#6b5a4e" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      <path d="M100 124 C110 134 126 132 134 124" stroke="#6b5a4e" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {/* Underbite with two little teeth */}
      <path d="M78 136 C88 146 112 146 122 136 C118 144 110 150 100 150 C90 150 82 144 78 136 Z" fill="#8f3f46" />
      <path d="M84 138 L88 130 L92 139 Z" fill="#ffffff" />
      <path d="M108 139 L112 130 L116 138 Z" fill="#ffffff" />
      {/* Nose */}
      <ellipse cx="100" cy="106" rx="17" ry="11" fill="#2a2320" />
      <ellipse cx="94" cy="103" rx="5" ry="2.5" fill="#ffffff" opacity="0.35" />

      {/* Collar with silver-and-gold tag */}
      <path d="M44 146 C70 164 130 164 156 146 L158 156 C130 176 70 176 42 156 Z" fill="#0b2a4f" />
      <circle cx="100" cy="170" r="10" fill={`url(#metal-${id})`} stroke="#9aa3ad" strokeWidth="1" />
      <text x="100" y="174" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="11" fill="#0b2a4f">
        Y
      </text>
    </svg>
  )
}
