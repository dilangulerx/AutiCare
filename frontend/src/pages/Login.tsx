import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate, Link } from 'react-router-dom'
import { AutiCareLogoHorizontal, LogoVariant3Spectrum } from '../components/AutiCareLogo'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {
      setError('Email veya şifre hatalı')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: "'Plus Jakarta Sans', Inter, system-ui, sans-serif", minHeight: '100vh', display: 'flex', background: '#F0FDFC' }}>

      {/* ─── SOL PANEL ─── */}
      <div style={{
        width: '48%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        padding: '44px 52px', position: 'relative', overflow: 'hidden',
        background: 'linear-gradient(150deg, #0D4F4F 0%, #0E7490 40%, #0891B2 70%, #5BB8D4 100%)'
      }}>
        {/* Dekoratif daireler */}
        <div style={{ position: 'absolute', top: -100, right: -100, width: 350, height: 350, borderRadius: '50%', background: 'rgba(125,211,216,0.1)' }} />
        <div style={{ position: 'absolute', bottom: 80, left: -80, width: 280, height: 280, borderRadius: '50%', background: 'rgba(91,184,212,0.12)' }} />

        {/* Logo */}
        <div style={{ position: 'relative', zIndex: 1, marginBottom: 40 }}>
          <AutiCareLogoHorizontal size={60} />
        </div>

        {/* Orta içerik */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: 40, fontWeight: 800, color: 'white', lineHeight: 1.15, marginBottom: 18, letterSpacing: -1.5 }}>
            Her küçük adım,<br />
            <span style={{ background: 'linear-gradient(90deg, #FCD34D, #86EFAC)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              büyük bir zafer!
            </span>
          </h1>

          <p style={{ color: 'rgba(207,250,254,0.85)', fontSize: 15, lineHeight: 1.75, marginBottom: 36 }}>
            Çocuğunuzun gelişimini sevgiyle takip edin.<br />
            Haftalık AI raporları ile ilerlemeyi birlikte keşfedin.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { icon: '📊', title: 'Günlük Davranış Kaydı', desc: 'Sadece 5 dakikada tamamlayın' },
              { icon: '🤖', title: 'Haftalık AI Raporu', desc: 'Destekleyici gelişim analizi' },
              { icon: '🔔', title: 'Akıllı Hatırlatıcılar', desc: 'İlaç ve randevu bildirimleri' },
            ].map(item => (
              <div key={item.title} style={{ display: 'flex', alignItems: 'center', gap: 14, background: 'rgba(255,255,255,0.06)', borderRadius: 16, padding: '13px 16px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <div style={{ width: 40, height: 40, background: 'rgba(255,255,255,0.12)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>
                  {item.icon}
                </div>
                <div>
                  <p style={{ color: 'white', fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{item.title}</p>
                  <p style={{ color: 'rgba(207,250,254,0.6)', fontSize: 12 }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alt uyarı */}
        <div style={{ position: 'relative', zIndex: 1, background: 'rgba(255,255,255,0.06)', borderRadius: 14, padding: '13px 16px', border: '1px solid rgba(255,255,255,0.1)' }}>
          <p style={{ color: 'rgba(207,250,254,0.55)', fontSize: 12, lineHeight: 1.6 }}>
            ⚕️ AutiCare tıbbi teşhis koymaz. Yalnızca ebeveynlerin çocuklarının gelişimini takip etmelerine yardımcı olmak amacıyla tasarlanmıştır.
          </p>
        </div>
      </div>

      {/* ─── SAĞ PANEL ─── */}
      <div style={{ width: '52%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px', background: '#FAFFFE' }}>
        <div style={{ width: '100%', maxWidth: 440 }}>

          {/* Merkezi logo */}
          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 18 }}>
              <LogoVariant3Spectrum size={120} />
            </div>
            <h2 style={{ fontSize: 27, fontWeight: 800, color: '#0D4F4F', marginBottom: 6, letterSpacing: -0.5 }}>
              Hoş geldiniz!
            </h2>
            <p style={{ color: '#6B7280', fontSize: 15 }}>
              <span style={{ color: '#0891B2', fontWeight: 700 }}>AutiCare</span> hesabınıza giriş yapın
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Email */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#374151', marginBottom: 8, letterSpacing: 0.3 }}>EMAIL ADRESİ</label>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', fontSize: 16, opacity: 0.5 }}>✉️</span>
                <input
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  style={{ width: '100%', padding: '15px 16px 15px 46px', borderRadius: 14, border: '2px solid #E5E7EB', fontSize: 15, color: '#1F2937', background: 'white', outline: 'none', boxSizing: 'border-box', transition: 'all 0.2s', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}
                  placeholder="ornek@email.com" required
                  onFocus={e => { e.target.style.borderColor = '#0891B2'; e.target.style.boxShadow = '0 0 0 4px rgba(8,145,178,0.1)' }}
                  onBlur={e => { e.target.style.borderColor = '#E5E7EB'; e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)' }}
                />
              </div>
            </div>

            {/* Şifre */}
            <div style={{ marginBottom: 28 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: '#374151', marginBottom: 8, letterSpacing: 0.3 }}>ŞİFRE</label>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)', fontSize: 16, opacity: 0.5 }}>🔒</span>
                <input
                  type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  style={{ width: '100%', padding: '15px 16px 15px 46px', borderRadius: 14, border: '2px solid #E5E7EB', fontSize: 15, color: '#1F2937', background: 'white', outline: 'none', boxSizing: 'border-box', transition: 'all 0.2s', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}
                  placeholder="••••••••" required
                  onFocus={e => { e.target.style.borderColor = '#0891B2'; e.target.style.boxShadow = '0 0 0 4px rgba(8,145,178,0.1)' }}
                  onBlur={e => { e.target.style.borderColor = '#E5E7EB'; e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)' }}
                />
              </div>
            </div>

            {error && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#FEF2F2', border: '1px solid #FECACA', color: '#DC2626', fontSize: 14, padding: '13px 16px', borderRadius: 12, marginBottom: 20 }}>
                <span>⚠️</span> {error}
              </div>
            )}

            <button type="submit" disabled={loading} style={{ width: '100%', padding: '16px', borderRadius: 14, border: 'none', background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #0891B2 0%, #5BB8D4 100%)', color: 'white', fontSize: 16, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', boxShadow: loading ? 'none' : '0 8px 24px rgba(8,145,178,0.4)', transition: 'all 0.2s' }}>
              {loading ? '⏳ Giriş yapılıyor...' : 'Giriş Yap →'}
            </button>
          </form>

          <div style={{ marginTop: 24, padding: '18px 20px', background: 'linear-gradient(135deg, #ECFEFF, #F0FDFA)', borderRadius: 16, border: '1px solid #A5F3FC', textAlign: 'center' }}>
            <p style={{ color: '#4B5563', fontSize: 14 }}>
              Hesabınız yok mu?{' '}
              <Link to="/register" style={{ color: '#0891B2', fontWeight: 700, textDecoration: 'none' }}>Ücretsiz Kayıt Olun →</Link>
            </p>
          </div>

          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 28 }}>
            {[{ icon: '🔒', text: 'Güvenli SSL' }, { icon: '🇹🇷', text: 'KVKK Uyumlu' }, { icon: '🏥', text: 'Gizli Veriler' }].map(badge => (
              <div key={badge.text} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
                <span style={{ fontSize: 20 }}>{badge.icon}</span>
                <span style={{ color: '#9CA3AF', fontSize: 11, fontWeight: 500 }}>{badge.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}