import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { AutiCareLogoHorizontal } from '../components/AutiCareLogo'
import type { Child } from '../api/children'
import { getChildren, createChild } from '../api/children'
import { getLogs, createLog } from '../api/logs'
import type { DailyLog } from '../api/logs'
import { getReports, generateReport } from '../api/reports'
import type { WeeklyReport } from '../api/reports'
import { getReminders, createReminder, deleteReminder } from '../api/reminders'
import type { Reminder } from '../api/reminders'
import { sendChatMessage, checkAnomaly } from '../api/ai'

type ActiveSection = 'overview' | 'daily-log' | 'reports' | 'reminders' | 'settings' | 'chat'

export default function Dashboard() {
  const { user, logout, updateUser } = useAuth()

  const [children, setChildren] = useState<Child[]>([])
  const [selectedChild, setSelectedChild] = useState<Child | null>(null)
  const [activeSection, setActiveSection] = useState<ActiveSection>('overview')
  const [logs, setLogs] = useState<DailyLog[]>([])
  const [reports, setReports] = useState<WeeklyReport[]>([])
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [loading, setLoading] = useState(true)

  const [showAddChild, setShowAddChild] = useState(false)
  const [newChildName, setNewChildName] = useState('')
  const [newChildBirth, setNewChildBirth] = useState('')
  const [newChildNotes, setNewChildNotes] = useState('')

  const [logForm, setLogForm] = useState({ eye_contact: 3, aggression_level: 1, communication_score: 3, sleep_hours: 8, notes: '', date: new Date().toISOString().split('T')[0] })
  const [logSaving, setLogSaving] = useState(false)
  const [logSuccess, setLogSuccess] = useState(false)

  const [reminderForm, setReminderForm] = useState({ title: '', reminder_type: 'general', remind_at: '', recur_type: 'none' })
  const [reminderSaving, setReminderSaving] = useState(false)

  const [reportGenerating, setReportGenerating] = useState(false)
  const [selectedReport, setSelectedReport] = useState<WeeklyReport | null>(null)

  const [darkMode, setDarkMode] = useState(false)
  const [settingsForm, setSettingsForm] = useState({ name: '', email: '', phone: '', password: '', confirmPassword: '' })
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsSuccess, setSettingsSuccess] = useState('')
  const [settingsError, setSettingsError] = useState('')

  const [chatMessages, setChatMessages] = useState<{role: 'user' | 'ai', text: string}[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  const [anomaly, setAnomaly] = useState<{has_anomaly: boolean, message: string} | null>(null)

  useEffect(() => { loadChildren() }, [])

  useEffect(() => {
    if (selectedChild) loadChildData(selectedChild.id)
  }, [selectedChild])

  useEffect(() => {
    if (user) setSettingsForm(prev => ({ ...prev, name: user.name, email: user.email, phone: user.phone || '' }))
  }, [user])

  const loadChildren = async () => {
    try {
      const res = await getChildren()
      setChildren(res.data)
      if (res.data.length > 0) setSelectedChild(res.data[0])
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const loadChildData = async (childId: number) => {
    try {
      const [logsRes, reportsRes, remindersRes] = await Promise.all([
        getLogs(childId), getReports(childId), getReminders(childId)
      ])
      setLogs(logsRes.data)
      setReports(reportsRes.data)
      setReminders(remindersRes.data)
      if (reportsRes.data.length > 0) setSelectedReport(reportsRes.data[0])
      
          // 
    const anomalyRes = await checkAnomaly(childId)
    setAnomaly(anomalyRes.data)
    } catch (e) { console.error(e) }
  }

  const handleAddChild = async () => {
    if (!newChildName || !newChildBirth) return
    try {
      const res = await createChild({ name: newChildName, birth_date: newChildBirth, notes: newChildNotes })
      setChildren([...children, res.data])
      setSelectedChild(res.data)
      setShowAddChild(false)
      setNewChildName(''); setNewChildBirth(''); setNewChildNotes('')
    } catch (e) { console.error(e) }
  }

  const handleSaveLog = async () => {
    if (!selectedChild) return
    setLogSaving(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      await createLog({ ...logForm, child_id: selectedChild.id, date: today })
      setLogSuccess(true)
      setTimeout(() => setLogSuccess(false), 3000)
      loadChildData(selectedChild.id)
    } catch (e) { console.error(e) }
    finally { setLogSaving(false) }
  }

  const handleGenerateReport = async () => {
    if (!selectedChild) return
    setReportGenerating(true)
    try {
      const monday = getMonday()
      const res = await generateReport(selectedChild.id, monday)
      setReports([res.data, ...reports])
      setSelectedReport(res.data)
    } catch (e) { console.error(e) }
    finally { setReportGenerating(false) }
  }

  const handleAddReminder = async () => {
    if (!selectedChild || !reminderForm.title || !reminderForm.remind_at) return
    setReminderSaving(true)
    try {
      const res = await createReminder({ ...reminderForm, child_id: selectedChild.id, is_active: true })
      setReminders([...reminders, res.data])
      setReminderForm({ title: '', reminder_type: 'general', remind_at: '', recur_type: 'none' })
    } catch (e) { console.error(e) }
    finally { setReminderSaving(false) }
  }

  const handleDeleteChild = async (id: number) => {
    if (!confirm('Bu çocuğu silmek istediğinizden emin misiniz? Tüm kayıtlar silinecek!')) return
    try {
      const { deleteChild } = await import('../api/children')
      await deleteChild(id)
      const updated = children.filter(c => c.id !== id)
      setChildren(updated)
      setSelectedChild(updated.length > 0 ? updated[0] : null)
    } catch (e) { console.error(e) }
  }



  const handleDeleteReminder = async (id: number) => {
    try {
      await deleteReminder(id)
      setReminders(reminders.filter(r => r.id !== id))
    } catch (e) { console.error(e) }
  }

  const handleSaveSettings = async () => {
    if (settingsForm.password && settingsForm.password !== settingsForm.confirmPassword) {
      setSettingsError('Şifreler eşleşmiyor!')
      return
    }
    setSettingsSaving(true)
    setSettingsError('')
    setSettingsSuccess('')
    try {
      const payload: { name?: string; email?: string; phone?: string; password?: string } = {}
      if (settingsForm.name) payload.name = settingsForm.name
      if (settingsForm.email) payload.email = settingsForm.email
      if (settingsForm.phone) payload.phone = settingsForm.phone
      if (settingsForm.password) payload.password = settingsForm.password
      await updateUser(payload)
      setSettingsSuccess('Bilgileriniz güncellendi!')
      setSettingsForm(prev => ({ ...prev, password: '', confirmPassword: '' }))
      setTimeout(() => setSettingsSuccess(''), 3000)
    } catch {
      setSettingsError('Güncelleme sırasında hata oluştu.')
    } finally {
      setSettingsSaving(false)
    }
  }

  const handleSendChat = async () => {
    if (!selectedChild || !chatInput.trim()) return
    const userMessage = chatInput.trim()
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setChatLoading(true)
    try {
      const res = await sendChatMessage(selectedChild.id, userMessage)
      setChatMessages(prev => [...prev, { role: 'ai', text: res.data.response }])
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'ai', text: 'Bir hata oluştu, tekrar deneyin.' }])
    } finally {
      setChatLoading(false)
    }
  }

  const getMonday = () => {
    const d = new Date()
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1)
    return new Date(d.setDate(diff)).toISOString().split('T')[0]
  }

  const getAge = (birthDate: string) => {
    const diff = Date.now() - new Date(birthDate).getTime()
    return Math.floor(diff / (1000 * 60 * 60 * 24 * 365))
  }

  const getLastLog = () => logs[logs.length - 1]

  const getAvg = (field: keyof DailyLog) => {
    if (!logs.length) return 0
    const last7 = logs.slice(-7)
    return (last7.reduce((sum, l) => sum + (Number(l[field]) || 0), 0) / last7.length).toFixed(1)
  }

  const scoreColor = (val: number, max = 5) => {
    const pct = val / max
    if (pct >= 0.7) return '#10B981'
    if (pct >= 0.4) return '#F59E0B'
    return '#EF4444'
  }

  const aggressionColor = (val: number) => {
    if (val <= 2) return '#10B981'
    if (val <= 3) return '#F59E0B'
    return '#EF4444'
  }

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F0FDFC' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🌱</div>
        <p style={{ color: '#0891B2', fontWeight: 600 }}>Yükleniyor...</p>
      </div>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', display: 'flex', fontFamily: "'Plus Jakarta Sans', Inter, system-ui, sans-serif", background: darkMode ? '#0F172A' : '#F0FDFC' }}>

      {/* ─── SOL SIDEBAR ─── */}
      <div style={{ width: 260, background: 'linear-gradient(180deg, #0D4F4F 0%, #0E7490 100%)', display: 'flex', flexDirection: 'column', padding: '24px 0', position: 'fixed', height: '100vh', zIndex: 10 }}>

        <div style={{ padding: '0 20px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <AutiCareLogoHorizontal size={36} />
        </div>

        <div style={{ padding: '20px 16px 12px', flex: 1, overflowY: 'auto' }}>
          <p style={{ color: 'rgba(207,250,254,0.6)', fontSize: 11, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 10, paddingLeft: 8 }}>
            Çocuklar
          </p>

          {children.map(child => (
            <div key={child.id} style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
              borderRadius: 12, marginBottom: 4, cursor: 'pointer', transition: 'all 0.2s',
              background: selectedChild?.id === child.id ? 'rgba(255,255,255,0.15)' : 'transparent',
              border: selectedChild?.id === child.id ? '1px solid rgba(255,255,255,0.2)' : '1px solid transparent',
              position: 'relative'
          }}>
            <div onClick={() => setSelectedChild(child)} style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
              <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #7DD3D8, #A5F3FC)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, flexShrink: 0 }}>
               👶
              </div>
            <div>
              <p style={{ color: 'white', fontWeight: 600, fontSize: 13 }}>{child.name}</p>
              <p style={{ color: 'rgba(207,250,254,0.6)', fontSize: 11 }}>{getAge(child.birth_date)} yaşında</p>
           </div>
        </div>
       <button
          onClick={(e) => { e.stopPropagation(); handleDeleteChild(child.id) }}
          style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6, padding: '3px 7px', color: 'rgba(255,255,255,0.45)', fontSize: 14, cursor: 'pointer', lineHeight: 1, flexShrink: 0 }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.3)'; e.currentTarget.style.color = 'white' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.45)' }}
       >
         ×
       </button>
     </div>
   ))}
          <button onClick={() => setShowAddChild(true)} style={{ width: '100%', padding: '10px 12px', borderRadius: 12, border: '1px dashed rgba(255,255,255,0.25)', background: 'transparent', color: 'rgba(207,250,254,0.7)', fontSize: 13, cursor: 'pointer', marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>+</span> Çocuk Ekle
          </button>

          <div style={{ marginTop: 24 }}>
            <p style={{ color: 'rgba(207,250,254,0.6)', fontSize: 11, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 10, paddingLeft: 8 }}>
              Menü
            </p>
            {[
              { id: 'overview', icon: '🏠', label: 'Genel Bakış' },
              { id: 'daily-log', icon: '📝', label: 'Günlük Kayıt' },
              { id: 'reports', icon: '🤖', label: 'AI Raporlar' },
              { id: 'reminders', icon: '🔔', label: 'Hatırlatıcılar' },
              { id: 'chat', icon: '💬', label: 'AI Asistan' },
              { id: 'settings', icon: '⚙️', label: 'Ayarlar' },
            ].map(item => (
              <button key={item.id} onClick={() => setActiveSection(item.id as ActiveSection)} style={{
                width: '100%', padding: '10px 12px', borderRadius: 12, border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 10, marginBottom: 2, transition: 'all 0.2s', textAlign: 'left',
                background: activeSection === item.id ? 'rgba(255,255,255,0.15)' : 'transparent',
                color: activeSection === item.id ? 'white' : 'rgba(207,250,254,0.7)',
                fontWeight: activeSection === item.id ? 600 : 400, fontSize: 13
              }}>
                <span>{item.icon}</span> {item.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ color: 'white', fontWeight: 600, fontSize: 13 }}>{user?.name}</p>
              <p style={{ color: 'rgba(207,250,254,0.6)', fontSize: 11 }}>{user?.email}</p>
            </div>
            <button onClick={logout} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: '6px 10px', color: 'rgba(207,250,254,0.8)', fontSize: 11, cursor: 'pointer' }}>
              Çıkış
            </button>
          </div>
        </div>
      </div>

      {/* ─── ANA İÇERİK ─── */}
      <div style={{ marginLeft: 260, flex: 1, padding: '32px', minHeight: '100vh' }}>

        {/* ─── AYARLAR ─── */}
        {activeSection === 'settings' && (
          <div style={{ maxWidth: 580 }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: darkMode ? '#E0F7FA' : '#0D4F4F', marginBottom: 6 }}>⚙️ Ayarlar</h1>
            <p style={{ color: '#6B7280', fontSize: 14, marginBottom: 28 }}>Hesap bilgilerinizi ve tercihlerinizi yönetin</p>

            <div style={{ background: darkMode ? '#1E293B' : 'white', borderRadius: 20, padding: '24px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)', marginBottom: 20 }}>
              <h3 style={{ fontWeight: 700, color: darkMode ? '#E0F7FA' : '#0D4F4F', fontSize: 15, marginBottom: 20 }}>🎨 Görünüm</h3>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <p style={{ fontWeight: 600, color: darkMode ? '#E0F7FA' : '#374151', fontSize: 14 }}>Karanlık Mod</p>
                  <p style={{ color: '#9CA3AF', fontSize: 12, marginTop: 2 }}>Arayüz rengini değiştir</p>
                </div>
                <div onClick={() => setDarkMode(!darkMode)} style={{ width: 52, height: 28, borderRadius: 14, cursor: 'pointer', transition: 'all 0.3s', position: 'relative', background: darkMode ? 'linear-gradient(135deg, #0891B2, #5BB8D4)' : '#E5E7EB' }}>
                  <div style={{ position: 'absolute', top: 3, left: darkMode ? 27 : 3, width: 22, height: 22, borderRadius: '50%', background: 'white', transition: 'all 0.3s', boxShadow: '0 2px 6px rgba(0,0,0,0.2)' }} />
                </div>
              </div>
            </div>

            <div style={{ background: darkMode ? '#1E293B' : 'white', borderRadius: 20, padding: '24px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)', marginBottom: 20 }}>
              <h3 style={{ fontWeight: 700, color: darkMode ? '#E0F7FA' : '#0D4F4F', fontSize: 15, marginBottom: 20 }}>👤 Profil Bilgileri</h3>
              {[
                { key: 'name', label: 'AD SOYAD', icon: '👤', type: 'text', placeholder: 'Adınız Soyadınız' },
                { key: 'email', label: 'EMAIL ADRESİ', icon: '✉️', type: 'email', placeholder: 'ornek@email.com' },
                { key: 'phone', label: 'TELEFON NUMARASI', icon: '📱', type: 'tel', placeholder: '+90 555 000 00 00' },
              ].map(field => (
                <div key={field.key} style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>{field.label}</label>
                  <div style={{ position: 'relative' }}>
                    <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 15, opacity: 0.5 }}>{field.icon}</span>
                    <input type={field.type} value={settingsForm[field.key as keyof typeof settingsForm]}
                      onChange={e => setSettingsForm({ ...settingsForm, [field.key]: e.target.value })}
                      placeholder={field.placeholder}
                      style={{ width: '100%', padding: '12px 14px 12px 42px', borderRadius: 12, border: '2px solid #E5E7EB', fontSize: 14, color: '#1F2937', background: darkMode ? '#0F172A' : 'white', outline: 'none', boxSizing: 'border-box' }}
                      onFocus={e => e.target.style.borderColor = '#0891B2'}
                      onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div style={{ background: darkMode ? '#1E293B' : 'white', borderRadius: 20, padding: '24px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)', marginBottom: 20 }}>
              <h3 style={{ fontWeight: 700, color: darkMode ? '#E0F7FA' : '#0D4F4F', fontSize: 15, marginBottom: 20 }}>🔒 Şifre Değiştir</h3>
              {[
                { key: 'password', label: 'YENİ ŞİFRE', placeholder: 'En az 6 karakter' },
                { key: 'confirmPassword', label: 'ŞİFRE TEKRAR', placeholder: 'Şifrenizi tekrar girin' },
              ].map(field => (
                <div key={field.key} style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#6B7280', display: 'block', marginBottom: 6, letterSpacing: 0.5 }}>{field.label}</label>
                  <div style={{ position: 'relative' }}>
                    <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 15, opacity: 0.5 }}>🔒</span>
                    <input type="password" value={settingsForm[field.key as keyof typeof settingsForm]}
                      onChange={e => setSettingsForm({ ...settingsForm, [field.key]: e.target.value })}
                      placeholder={field.placeholder}
                      style={{ width: '100%', padding: '12px 14px 12px 42px', borderRadius: 12, border: '2px solid #E5E7EB', fontSize: 14, color: '#1F2937', background: darkMode ? '#0F172A' : 'white', outline: 'none', boxSizing: 'border-box' }}
                      onFocus={e => e.target.style.borderColor = '#0891B2'}
                      onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                    />
                  </div>
                </div>
              ))}
            </div>

            {settingsSuccess && (
              <div style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', padding: '12px 16px', borderRadius: 12, marginBottom: 16, fontSize: 14 }}>✅ {settingsSuccess}</div>
            )}
            {settingsError && (
              <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', color: '#DC2626', padding: '12px 16px', borderRadius: 12, marginBottom: 16, fontSize: 14 }}>⚠️ {settingsError}</div>
            )}

            <button onClick={handleSaveSettings} disabled={settingsSaving} style={{ width: '100%', padding: '15px', borderRadius: 14, border: 'none', background: settingsSaving ? '#9CA3AF' : 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontSize: 16, fontWeight: 700, cursor: settingsSaving ? 'not-allowed' : 'pointer', boxShadow: '0 6px 20px rgba(8,145,178,0.3)' }}>
              {settingsSaving ? '⏳ Kaydediliyor...' : 'Değişiklikleri Kaydet'}
            </button>
          </div>
        )}

        {/* ─── DIGER SAYFALAR ─── */}
        {activeSection !== 'settings' && (
          <>
            {!selectedChild ? (
              <div style={{ textAlign: 'center', marginTop: 80 }}>
                <div style={{ fontSize: 64, marginBottom: 16 }}>👶</div>
                <h2 style={{ fontSize: 24, fontWeight: 700, color: '#0D4F4F', marginBottom: 8 }}>Henüz çocuk eklenmedi</h2>
                <p style={{ color: '#6B7280', marginBottom: 24 }}>Sol panelden çocuk ekleyerek başlayın</p>
                <button onClick={() => setShowAddChild(true)} style={{ padding: '12px 24px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontWeight: 600, cursor: 'pointer' }}>
                  + Çocuk Ekle
                </button>
              </div>
            ) : (
              <>
                {/* ─── GENEL BAKIS ─── */}
                {activeSection === 'overview' && (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
                      <div>
                        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#0D4F4F', marginBottom: 4 }}>Hoş geldiniz, {user?.name}! 👋</h1>
                        <p style={{ color: '#6B7280', fontSize: 14 }}>{selectedChild.name} için genel bakış</p>
                      </div>
                      <div style={{ background: 'white', borderRadius: 16, padding: '12px 20px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'linear-gradient(135deg, #7DD3D8, #5BB8D4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>👶</div>
                        <div>
                          <p style={{ fontWeight: 700, color: '#0D4F4F', fontSize: 15 }}>{selectedChild.name}</p>
                          <p style={{ color: '#6B7280', fontSize: 12 }}>{getAge(selectedChild.birth_date)} yaşında</p>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
                      {[
                        { label: 'Göz Teması', value: getAvg('eye_contact'), max: 5, icon: '👁️', color: scoreColor(Number(getAvg('eye_contact'))) },
                        { label: 'İletişim', value: getAvg('communication_score'), max: 5, icon: '💬', color: scoreColor(Number(getAvg('communication_score'))) },
                        { label: 'Agresyon', value: getAvg('aggression_level'), max: 5, icon: '😤', color: aggressionColor(Number(getAvg('aggression_level'))) },
                        { label: 'Uyku', value: getAvg('sleep_hours'), max: 12, icon: '😴', color: scoreColor(Number(getAvg('sleep_hours')), 12) },
                      ].map(card => (
                        <div key={card.label} style={{ background: 'white', borderRadius: 16, padding: '20px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', borderTop: `3px solid ${card.color}` }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                            <span style={{ fontSize: 22 }}>{card.icon}</span>
                            <span style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 500 }}>Son 7 gün</span>
                          </div>
                          <p style={{ fontSize: 28, fontWeight: 800, color: card.color }}>{card.value}</p>
                          <p style={{ fontSize: 12, color: '#6B7280', marginTop: 2 }}>{card.label} <span style={{ color: '#9CA3AF' }}>/ {card.max}</span></p>
                        </div>
                      ))}
                    </div>

                    {anomaly && anomaly.has_anomaly && (
                    <div style={{
                      background: 'linear-gradient(135deg, #FEF2F2, #FFF5F5)',
                      border: '1px solid #FECACA',
                      borderLeft: '4px solid #EF4444',
                      borderRadius: 16, padding: '20px 24px',
                      marginBottom: 24,
                      display: 'flex', alignItems: 'flex-start', gap: 16
                    }}>
                    <div style={{ fontSize: 28, flexShrink: 0 }}>⚠️</div>
                     <div>
                      <h4 style={{ color: '#DC2626', fontWeight: 700, fontSize: 15, marginBottom: 6 }}>
                       Anomali Tespit Edildi!
                      </h4>
                      <p style={{ color: '#7F1D1D', fontSize: 13, lineHeight: 1.7 }}>
                       {anomaly.message}
                      </p>
                      <button
                       onClick={() => setActiveSection('chat')}
                       style={{ marginTop: 12, background: '#EF4444', border: 'none', borderRadius: 8, padding: '8px 16px', color: 'white', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                       💬 AI Asistan'a Sor →
                      </button>
                     </div>
                    </div>
                    )}

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                      <div style={{ background: 'white', borderRadius: 16, padding: '24px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                          <h3 style={{ fontWeight: 700, color: '#0D4F4F', fontSize: 15 }}>📝 Son Kayıt</h3>
                          <button onClick={() => setActiveSection('daily-log')} style={{ fontSize: 12, color: '#0891B2', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Yeni Ekle →</button>
                        </div>
                        {getLastLog() ? (
                          <div>
                            <p style={{ color: '#9CA3AF', fontSize: 12, marginBottom: 12 }}>{getLastLog().date}</p>
                            {[
                              { label: 'Göz Teması', value: getLastLog().eye_contact, max: 5 },
                              { label: 'İletişim', value: getLastLog().communication_score, max: 5 },
                              { label: 'Agresyon', value: getLastLog().aggression_level, max: 5 },
                            ].map(item => (
                              <div key={item.label} style={{ marginBottom: 10 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                  <span style={{ fontSize: 12, color: '#374151' }}>{item.label}</span>
                                  <span style={{ fontSize: 12, fontWeight: 600, color: '#0D4F4F' }}>{item.value}/{item.max}</span>
                                </div>
                                <div style={{ height: 6, background: '#F3F4F6', borderRadius: 4 }}>
                                  <div style={{ height: '100%', borderRadius: 4, background: 'linear-gradient(90deg, #0891B2, #5BB8D4)', width: `${(item.value / item.max) * 100}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p style={{ color: '#9CA3AF', fontSize: 13 }}>Henüz kayıt yok</p>
                        )}
                      </div>

                      <div style={{ background: 'white', borderRadius: 16, padding: '24px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                          <h3 style={{ fontWeight: 700, color: '#0D4F4F', fontSize: 15 }}>🤖 Son AI Raporu</h3>
                          <button onClick={() => setActiveSection('reports')} style={{ fontSize: 12, color: '#0891B2', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Tümünü Gör →</button>
                        </div>
                        {selectedReport ? (
                          <div>
                            <p style={{ color: '#9CA3AF', fontSize: 12, marginBottom: 10 }}>{selectedReport.week_start_date} haftası</p>
                            <p style={{ color: '#374151', fontSize: 13, lineHeight: 1.6, display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{selectedReport.report_text}</p>
                          </div>
                        ) : (
                          <div>
                            <p style={{ color: '#9CA3AF', fontSize: 13, marginBottom: 12 }}>Henüz rapor yok</p>
                            <button onClick={handleGenerateReport} disabled={reportGenerating} style={{ padding: '8px 16px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                              {reportGenerating ? '⏳ Oluşturuluyor...' : '🤖 Rapor Oluştur'}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* ─── GÜNLÜK KAYIT ─── */}
                {activeSection === 'daily-log' && (
                  <div style={{ maxWidth: 600 }}>
                    <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0D4F4F', marginBottom: 6 }}>📝 Günlük Kayıt</h1>
                    <p style={{ color: '#6B7280', fontSize: 14, marginBottom: 28 }}>{selectedChild.name} için bugünün kaydı — {new Date().toLocaleDateString('tr-TR')}</p>

                    <div style={{ background: 'white', borderRadius: 20, padding: '28px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)' }}>
                      {[
                        { key: 'eye_contact', label: 'Göz Teması', icon: '👁️', desc: '1 = Hiç, 5 = Çok iyi' },
                        { key: 'communication_score', label: 'İletişim Skoru', icon: '💬', desc: '1 = Zor, 5 = Mükemmel' },
                        { key: 'aggression_level', label: 'Agresyon Seviyesi', icon: '😤', desc: '1 = Sakin, 5 = Çok agresif' },
                      ].map(item => (
                        <div key={item.key} style={{ marginBottom: 24 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <label style={{ fontWeight: 600, color: '#0D4F4F', fontSize: 14 }}>{item.icon} {item.label}</label>
                            <div style={{ background: 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', borderRadius: 8, padding: '2px 10px', fontSize: 14, fontWeight: 700 }}>
                              {logForm[item.key as keyof typeof logForm]}
                            </div>
                          </div>
                          <p style={{ color: '#9CA3AF', fontSize: 11, marginBottom: 8 }}>{item.desc}</p>
                          <input type="range" min={1} max={5} step={1}
                            value={logForm[item.key as keyof typeof logForm] as number}
                            onChange={e => setLogForm({ ...logForm, [item.key]: Number(e.target.value) })}
                            style={{ width: '100%', accentColor: '#0891B2' }}
                          />
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
                            {[1,2,3,4,5].map(n => <span key={n} style={{ fontSize: 10, color: '#D1D5DB' }}>{n}</span>)}
                          </div>
                        </div>
                      ))}
                      <div style={{ marginBottom: 24 }}>
                        <label style={{ fontWeight: 600, color: '#0D4F4F', fontSize: 14, display: 'block', marginBottom: 8 }}>📅 Tarih</label>
                         <input
                           type="date"
                           value={logForm.date}
                           max={new Date().toISOString().split('T')[0]}
                           onChange={e => setLogForm({ ...logForm, date: e.target.value })}
                           style={{ width: '100%', padding: '10px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                           onFocus={e => e.target.style.borderColor = '#0891B2'}
                           onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                          />
                        </div>

                      <div style={{ marginBottom: 24 }}>
                        <label style={{ fontWeight: 600, color: '#0D4F4F', fontSize: 14, display: 'block', marginBottom: 8 }}>😴 Uyku Süresi</label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <input type="number" min={0} max={24} step={0.5} value={logForm.sleep_hours}
                            onChange={e => setLogForm({ ...logForm, sleep_hours: Number(e.target.value) })}
                            style={{ width: 100, padding: '10px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 15, fontWeight: 600, color: '#0D4F4F', outline: 'none' }}
                          />
                          <span style={{ color: '#6B7280', fontSize: 14 }}>saat</span>
                        </div>
                      </div>

                      <div style={{ marginBottom: 28 }}>
                        <label style={{ fontWeight: 600, color: '#0D4F4F', fontSize: 14, display: 'block', marginBottom: 8 }}>📋 Günlük Notlar</label>
                        <textarea value={logForm.notes} onChange={e => setLogForm({ ...logForm, notes: e.target.value })}
                          placeholder="Bugün neler yaşandı? Özel gözlemleriniz..."
                          style={{ width: '100%', padding: '12px 16px', borderRadius: 12, border: '2px solid #E5E7EB', fontSize: 14, color: '#374151', outline: 'none', resize: 'vertical', minHeight: 100, boxSizing: 'border-box', fontFamily: 'inherit' }}
                          onFocus={e => e.target.style.borderColor = '#0891B2'}
                          onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                        />
                      </div>

                      {logSuccess && (
                        <div style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', padding: '12px 16px', borderRadius: 12, marginBottom: 16, fontSize: 14 }}>
                          ✅ Kayıt başarıyla kaydedildi!
                        </div>
                      )}

                      <button onClick={handleSaveLog} disabled={logSaving} style={{ width: '100%', padding: '15px', borderRadius: 14, border: 'none', background: logSaving ? '#9CA3AF' : 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontSize: 16, fontWeight: 700, cursor: logSaving ? 'not-allowed' : 'pointer', boxShadow: '0 6px 20px rgba(8,145,178,0.3)' }}>
                        {logSaving ? '⏳ Kaydediliyor...' : ' Kaydet'}
                      </button>
                    </div>
                  </div>
                )}

                {/* ─── RAPORLAR ─── */}
                {activeSection === 'reports' && (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
                      <div>
                        <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0D4F4F', marginBottom: 4 }}>🤖 AI Raporlar</h1>
                        <p style={{ color: '#6B7280', fontSize: 14 }}>{selectedChild.name} için haftalık gelişim raporları</p>
                      </div>
                      <button onClick={handleGenerateReport} disabled={reportGenerating} style={{ padding: '12px 20px', borderRadius: 12, border: 'none', background: reportGenerating ? '#9CA3AF' : 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontWeight: 600, cursor: reportGenerating ? 'not-allowed' : 'pointer', fontSize: 14, boxShadow: '0 4px 14px rgba(8,145,178,0.3)' }}>
                        {reportGenerating ? '⏳ Oluşturuluyor...' : '+ Bu Hafta Rapor Oluştur'}
                      </button>
                    </div>

                    {reports.length === 0 ? (
                      <div style={{ textAlign: 'center', marginTop: 60 }}>
                        <div style={{ fontSize: 56, marginBottom: 16 }}>🤖</div>
                        <h3 style={{ color: '#0D4F4F', fontWeight: 700, marginBottom: 8 }}>Henüz rapor yok</h3>
                        <p style={{ color: '#6B7280', fontSize: 14 }}>Günlük kayıtlar ekleyip haftalık rapor oluşturabilirsiniz</p>
                      </div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
                        <div>
                          {reports.map(report => (
                            <div key={report.id} onClick={() => setSelectedReport(report)} style={{
                              background: selectedReport?.id === report.id ? 'white' : 'rgba(255,255,255,0.6)',
                              borderRadius: 14, padding: '16px', marginBottom: 8, cursor: 'pointer',
                              border: selectedReport?.id === report.id ? '2px solid #0891B2' : '2px solid transparent',
                              boxShadow: selectedReport?.id === report.id ? '0 4px 14px rgba(8,145,178,0.15)' : 'none'
                            }}>
                              <p style={{ fontWeight: 600, color: '#0D4F4F', fontSize: 13 }}>
                                {new Date(report.week_start_date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })} haftası
                              </p>
                              <p style={{ color: '#9CA3AF', fontSize: 11, marginTop: 4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                {report.report_text?.replace(/\*\*(.+?)\*\*/g, '$1').substring(0, 80)}...
                              </p>
                            </div>
                          ))}
                        </div>

                        {selectedReport && (
                          <div style={{ background: 'white', borderRadius: 20, padding: '28px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)' }}>
                            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0D4F4F', marginBottom: 4 }}>
                              {new Date(selectedReport.week_start_date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })} Haftası
                            </h3>
                            <p style={{ color: '#9CA3AF', fontSize: 13, marginBottom: 20 }}>{selectedChild.name} için haftalık analiz</p>
                            <div 
                              style={{ color: '#374151', fontSize: 14, lineHeight: 1.8, marginBottom: 24 }}
                              dangerouslySetInnerHTML={{ __html: '<p>' + selectedReport.report_text
                                .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#0D4F4F">$1</strong>')
                                .replace(/\n\n/g, '</p><p style="margin-bottom:12px">')
                                .replace(/\n/g, '<br/>') + '</p>'
                              }}
                            />

                            {selectedReport.recommendations && (
                              <div>
                                <h4 style={{ fontWeight: 700, color: '#0D4F4F', marginBottom: 12, fontSize: 14 }}>✅ Öneriler</h4>
                                {selectedReport.recommendations.map((rec, i) => (
                                  <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8, alignItems: 'flex-start' }}>
                                    <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>{i + 1}</div>
                                    <p style={{ color: '#374151', fontSize: 13, lineHeight: 1.6 }}>{rec}</p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* ─── AI ASISTAN ─── */}
                {activeSection === 'chat' && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
                    <div style={{ marginBottom: 24 }}>
                      <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0D4F4F', marginBottom: 4 }}>💬 AI Asistan</h1>
                      <p style={{ color: '#6B7280', fontSize: 14 }}>{selectedChild.name} hakkında sorularınızı sorun</p>
                    </div>

                  {/* Mesajlar */}
                  <div style={{ flex: 1, overflowY: 'auto', background: 'white', borderRadius: 20, padding: '24px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)', marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {chatMessages.length === 0 && (
                      <div style={{ textAlign: 'center', marginTop: 60 }}>
                        <div style={{ fontSize: 56, marginBottom: 16 }}>🤖</div>
                        <h3 style={{ color: '#0D4F4F', fontWeight: 700, marginBottom: 8 }}>AI Asistanınız hazır!</h3>
                        <p style={{ color: '#6B7280', fontSize: 14 }}>{selectedChild.name} hakkında her şeyi sorabilirsiniz</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 24, maxWidth: 400, margin: '24px auto 0' }}>
                          {[
                            `${selectedChild.name}'in bu haftaki gelişimi nasıl?`,
                             'Göz teması geliştirmek için ne yapabilirim?',
                             'Uyku düzeni normal mi?'
                            ].map(q => (
                              <button key={q} onClick={() => setChatInput(q)}
                                style={{ background: '#F0FDFC', border: '1px solid #A5F3FC', borderRadius: 10, padding: '10px 16px', color: '#0891B2', fontSize: 13, cursor: 'pointer', textAlign: 'left' }}>
                                {q}
                              </button>
                            ))}
                          </div>
                        </div>
                       )}

                      {chatMessages.map((msg, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                          {msg.role === 'ai' && (
                            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #0D4F4F, #0891B2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, flexShrink: 0, marginRight: 10 }}>
                              🤖
                            </div>
                          )}
                         <div style={{
                           maxWidth: '70%', padding: '12px 16px', borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                           background: msg.role === 'user' ? 'linear-gradient(135deg, #0891B2, #5BB8D4)' : '#F8FAFC',
                           color: msg.role === 'user' ? 'white' : '#374151',
                           fontSize: 14, lineHeight: 1.6,
                           boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                          }}>
                          {msg.role === 'user' ? msg.text : (
                          <div dangerouslySetInnerHTML={{ __html: msg.text
                          .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#0D4F4F">$1</strong>')
                          .replace(/\n\n/g, '</p><p style="margin-bottom:8px">')
                          .replace(/\n/g, '<br/>')
                          .replace(/^(\d+)\.\s/gm, '<br/><strong style="color:#0891B2">$1.</strong> ')
                          }} />
                         )}
                         </div>
                         </div>
                       ))}

                       {chatLoading && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #0D4F4F, #0891B2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>🤖</div>
                          <div style={{ background: '#F8FAFC', borderRadius: '18px 18px 18px 4px', padding: '12px 16px', color: '#9CA3AF', fontSize: 14 }}>
                            ⏳ Düşünüyor...
                          </div>
                        </div>
                       )}
                     </div>

                     {/* Input */}
                     <div style={{ display: 'flex', gap: 12 }}>
                      <input
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSendChat()}
                        placeholder={`${selectedChild.name} hakkında bir şey sorun...`}
                        style={{ flex: 1, padding: '14px 18px', borderRadius: 14, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', fontFamily: 'inherit' }}
                        onFocus={e => e.target.style.borderColor = '#0891B2'}
                        onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                      />
                      <button onClick={handleSendChat} disabled={chatLoading || !chatInput.trim()}
                        style={{ padding: '14px 24px', borderRadius: 14, border: 'none', background: chatLoading ? '#9CA3AF' : 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontWeight: 700, cursor: chatLoading ? 'not-allowed' : 'pointer', fontSize: 14, boxShadow: '0 4px 14px rgba(8,145,178,0.3)' }}>
                         Gönder →
                      </button>
                    </div>
                 </div>
                )}
                 
                {/* ─── HATIRLATICLAR ─── */}
                {activeSection === 'reminders' && (
                  <div>
                    <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0D4F4F', marginBottom: 6 }}>🔔 Hatırlatıcılar</h1>
                    <p style={{ color: '#6B7280', fontSize: 14, marginBottom: 28 }}>{selectedChild.name} için ilaç, randevu ve aktivite hatırlatıcıları</p>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                      <div style={{ background: 'white', borderRadius: 20, padding: '24px', boxShadow: '0 2px 16px rgba(0,0,0,0.06)' }}>
                        <h3 style={{ fontWeight: 700, color: '#0D4F4F', fontSize: 15, marginBottom: 20 }}>+ Yeni Hatırlatıcı</h3>

                        <div style={{ marginBottom: 16 }}>
                          <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>BAŞLIK</label>
                          <input value={reminderForm.title} onChange={e => setReminderForm({ ...reminderForm, title: e.target.value })}
                            placeholder="ör. İlaç zamanı, Terapi seansı..."
                            style={{ width: '100%', padding: '11px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                            onFocus={e => e.target.style.borderColor = '#0891B2'}
                            onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                          />
                        </div>

                        <div style={{ marginBottom: 16 }}>
                          <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>TÜR</label>
                          <select value={reminderForm.reminder_type} onChange={e => setReminderForm({ ...reminderForm, reminder_type: e.target.value })}
                            style={{ width: '100%', padding: '11px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', background: 'white' }}>
                            <option value="general">Genel</option>
                            <option value="medication">💊 İlaç</option>
                            <option value="therapy">🏥 Terapi</option>
                            <option value="activity">🎯 Aktivite</option>
                          </select>
                        </div>

                        <div style={{ marginBottom: 16 }}>
                          <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>TARİH & SAAT</label>
                          <input type="datetime-local" value={reminderForm.remind_at} onChange={e => setReminderForm({ ...reminderForm, remind_at: e.target.value })}
                            style={{ width: '100%', padding: '11px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                            onFocus={e => e.target.style.borderColor = '#0891B2'}
                            onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                          />
                        </div>

                        <div style={{ marginBottom: 20 }}>
                          <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>TEKRAR</label>
                          <select value={reminderForm.recur_type} onChange={e => setReminderForm({ ...reminderForm, recur_type: e.target.value })}
                            style={{ width: '100%', padding: '11px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', background: 'white' }}>
                            <option value="none">Tekrar Yok</option>
                            <option value="daily">Her Gün</option>
                            <option value="weekly">Her Hafta</option>
                          </select>
                        </div>

                        <button onClick={handleAddReminder} disabled={reminderSaving} style={{ width: '100%', padding: '13px', borderRadius: 12, border: 'none', background: reminderSaving ? '#9CA3AF' : 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontWeight: 600, cursor: reminderSaving ? 'not-allowed' : 'pointer', fontSize: 14 }}>
                          {reminderSaving ? '⏳ Ekleniyor...' : '+ Hatırlatıcı Ekle'}
                        </button>
                      </div>

                      <div>
                        <h3 style={{ fontWeight: 700, color: '#0D4F4F', fontSize: 15, marginBottom: 16 }}>Aktif Hatırlatıcılar</h3>
                        {reminders.length === 0 ? (
                          <div style={{ background: 'white', borderRadius: 16, padding: '32px', textAlign: 'center', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
                            <div style={{ fontSize: 40, marginBottom: 12 }}>🔔</div>
                            <p style={{ color: '#9CA3AF', fontSize: 13 }}>Henüz hatırlatıcı yok</p>
                          </div>
                        ) : (
                          reminders.map(reminder => (
                            <div key={reminder.id} style={{ background: 'white', borderRadius: 14, padding: '16px 20px', marginBottom: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, #ECFEFF, #CFFAFE)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>
                                  {reminder.reminder_type === 'medication' ? '💊' : reminder.reminder_type === 'therapy' ? '🏥' : reminder.reminder_type === 'activity' ? '🎯' : '🔔'}
                                </div>
                                <div>
                                  <p style={{ fontWeight: 600, color: '#0D4F4F', fontSize: 13 }}>{reminder.title}</p>
                                  <p style={{ color: '#9CA3AF', fontSize: 11 }}>{new Date(reminder.remind_at).toLocaleString('tr-TR')}</p>
                                </div>
                              </div>
                              <button onClick={() => handleDeleteReminder(reminder.id)} style={{ background: '#FEF2F2', border: 'none', borderRadius: 8, padding: '6px 10px', color: '#EF4444', fontSize: 12, cursor: 'pointer' }}>
                                Sil
                              </button>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>

      {/* ─── ÇOCUK EKLEME  ─── */}
      {showAddChild && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'white', borderRadius: 20, padding: '32px', width: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <h3 style={{ fontSize: 20, fontWeight: 800, color: '#0D4F4F', marginBottom: 6 }}>👶 Çocuk Ekle</h3>
            <p style={{ color: '#6B7280', fontSize: 13, marginBottom: 24 }}>Yeni profil oluşturun</p>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>AD SOYAD</label>
              <input value={newChildName} onChange={e => setNewChildName(e.target.value)} placeholder="Çocuğunuzun adı"
                style={{ width: '100%', padding: '12px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                onFocus={e => e.target.style.borderColor = '#0891B2'} onBlur={e => e.target.style.borderColor = '#E5E7EB'}
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>DOĞUM TARİHİ</label>
              <input type="date" value={newChildBirth} onChange={e => setNewChildBirth(e.target.value)}
                style={{ width: '100%', padding: '12px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                onFocus={e => e.target.style.borderColor = '#0891B2'} onBlur={e => e.target.style.borderColor = '#E5E7EB'}
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 6 }}>NOTLAR (opsiyonel)</label>
              <textarea value={newChildNotes} onChange={e => setNewChildNotes(e.target.value)} placeholder="Tanı, ilaçlar, özel durumlar..."
                style={{ width: '100%', padding: '12px 14px', borderRadius: 10, border: '2px solid #E5E7EB', fontSize: 14, outline: 'none', resize: 'none', minHeight: 80, boxSizing: 'border-box', fontFamily: 'inherit' }}
                onFocus={e => e.target.style.borderColor = '#0891B2'} onBlur={e => e.target.style.borderColor = '#E5E7EB'}
              />
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setShowAddChild(false)} style={{ flex: 1, padding: '13px', borderRadius: 12, border: '2px solid #E5E7EB', background: 'white', color: '#6B7280', fontWeight: 600, cursor: 'pointer', fontSize: 14 }}>
                İptal
              </button>
              <button onClick={handleAddChild} style={{ flex: 2, padding: '13px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg, #0891B2, #5BB8D4)', color: 'white', fontWeight: 600, cursor: 'pointer', fontSize: 14 }}>
                Ekle →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}