import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-indigo-700">🌟 Gelişim Takip</h1>
          <button
            onClick={logout}
            className="bg-red-100 text-red-600 px-4 py-2 rounded-lg hover:bg-red-200 transition"
          >
            Çıkış Yap
          </button>
        </div>
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800">Hoş geldiniz, {user?.name}! 👋</h2>
          <p className="text-gray-500 mt-2">Dashboard yakında hazır olacak.</p>
        </div>
      </div>
    </div>
  )
}