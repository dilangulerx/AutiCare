import logoImg from '../assets/logo.png'

export function AutiCareIcon({ size = 76 }: { size?: number }) {
  return (
    <img src={logoImg} style={{ width: size, height: size, borderRadius: size * 0.22, flexShrink: 0 }} />
  )
}

export function AutiCareLogoHorizontal({ size = 44, darkText = false }: { size?: number; darkText?: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
      <AutiCareIcon size={size} />
      <div>
        <p style={{ color: darkText ? '#1E1B4B' : 'white', fontWeight: 800, fontSize: size * 0.43, letterSpacing: -0.3, lineHeight: 1 }}>
          Auti<span style={{ color: darkText ? '#5BB8D4' : '#A5F3FC' }}>Care</span>
        </p>
        <p style={{ color: darkText ? '#9CA3AF' : 'rgba(196,181,253,0.75)', fontSize: size * 0.24, fontWeight: 500, letterSpacing: 1.5, textTransform: 'uppercase' }}>
          Gelişim Takip
        </p>
      </div>
    </div>
  )
}

export function LogoVariant3Spectrum({ size = 76 }: { size?: number }) {
  return <AutiCareIcon size={size} />
}

export function LogoVariant1Modern({ size = 76 }: { size?: number }) {
  return <AutiCareIcon size={size} />
}

export function LogoVariant2Compassionate({ size = 76 }: { size?: number }) {
  return <AutiCareIcon size={size} />
}

export function LogoVariant4Professional({ size = 76 }: { size?: number }) {
  return <AutiCareIcon size={size} />
}