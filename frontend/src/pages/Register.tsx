import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate, Link } from 'react-router-dom'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(email, name, password)
      navigate('/dashboard')
    } catch {
      setError('Kayıt olurken hata oluştu. Email zaten kullanımda olabilir.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: "'Georgia', serif" }} className="min-h-screen flex">
      {/* Sol panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)' }}>
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15) 0%, transparent 50%),
                           radial-gradient(circle at 80% 20%, rgba(255, 183, 77, 0.1) 0%, transparent 40%),
                           radial-gradient(circle at 60% 80%, rgba(100, 181, 246, 0.1) 0%, transparent 40%)`
        }} />
        <div className="absolute top-20 left-20 w-32 h-32 rounded-full border border-white opacity-5" />
        <div className="absolute top-32 left-32 w-48 h-48 rounded-full border border-white opacity-5" />
        <div className="absolute bottom-40 right-20 w-64 h-64 rounded-full border border-white opacity-5" />

        <div className="relative z-10 flex flex-col justify-center px-16 text-white">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" style={{ background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                🌱
              </div>
              <span className="text-xl font-light tracking-widest uppercase opacity-80">Gelişim Takip</span>
            </div>
            <h1 className="text-5xl font-light leading-tight mb-6" style={{ letterSpacing: '-1px' }}>
              Yolculuğunuz<br />
              <span style={{ color: '#FFB74D' }}>bugün başlıyor.</span>
            </h1>
            <p className="text-lg opacity-60 font-light leading-relaxed">
              Ücretsiz hesap oluşturun ve çocuğunuzun<br />
              gelişimini takip etmeye başlayın.
            </p>
          </div>

          <div className="bg-white bg-opacity-5 rounded-2xl p-6 border border-white border-opacity-10">
            <p className="text-sm opacity-60 font-light italic leading-relaxed">
              "Bu uygulama tıbbi teşhis koymaz. Yalnızca günlük gözlemlerinizi kaydetmenize ve takip etmenize yardımcı olur."
            </p>
          </div>
        </div>
      </div>

      {/* Sağ panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8" style={{ background: '#FAFAF8' }}>
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-10">
            <span className="text-2xl">🌱</span>
            <span className="text-lg font-light tracking-widest uppercase text-gray-500">Gelişim Takip</span>
          </div>

          <h2 className="text-4xl font-light text-gray-900 mb-2" style={{ letterSpacing: '-1px' }}>
            Hesap oluşturun
          </h2>
          <p className="text-gray-400 mb-10 font-light">Birkaç dakikada başlayın</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-widest mb-2">
                Ad Soyad
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border-0 border-b-2 border-gray-200 bg-transparent px-0 py-3 text-gray-900 focus:outline-none focus:border-gray-900 transition-colors"
                placeholder="Adınız Soyadınız"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-widest mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border-0 border-b-2 border-gray-200 bg-transparent px-0 py-3 text-gray-900 focus:outline-none focus:border-gray-900 transition-colors"
                placeholder="ornek@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-widest mb-2">
                Şifre
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border-0 border-b-2 border-gray-200 bg-transparent px-0 py-3 text-gray-900 focus:outline-none focus:border-gray-900 transition-colors"
                placeholder="En az 6 karakter"
                required
                minLength={6}
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-100 text-red-600 text-sm px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 text-white font-light tracking-widest uppercase text-sm transition-all disabled:opacity-50"
                style={{ background: loading ? '#999' : '#1a1a2e', borderRadius: '4px' }}
              >
                {loading ? 'Kaydediliyor...' : 'Hesap Oluştur →'}
              </button>
            </div>
          </form>

          <p className="text-center text-sm text-gray-400 mt-8 font-light">
            Zaten hesabınız var mı?{' '}
            <Link to="/login" className="text-gray-900 font-medium hover:underline">
              Giriş Yapın
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}