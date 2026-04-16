/**
 * HumanReviewPanel — İnsan-Döngüde (HITL) Onay Paneli
 * 
 * NEDEN BU BİLEŞEN?
 * AI tarafından üretilen kritik çıktılar (terapi önerileri, anomali raporları)
 * bir insan uzman tarafından onaylanmalı. Bu panel:
 * 
 * 1. Bekleyen onayları listeler
 * 2. AI çıktısını ve güven skorunu gösterir
 * 3. Onaylama / Reddetme / Düzenleme seçenekleri sunar
 * 4. Uzman notları eklenebilir
 * 
 * Böylece yanlış pozitif anomali tespitleri veya uygunsuz terapi
 * önerileri ebeveynlere ulaşmadan düzeltilebilir.
 */

import { useState, useEffect } from 'react'
import type { HumanReview } from '../api/ai'
import { getPendingReviews, getAllReviews, updateReview } from '../api/ai'

interface Props {
  childId: number
}

export function HumanReviewPanel({ childId }: Props) {
  const [reviews, setReviews] = useState<HumanReview[]>([])
  const [historyReviews, setHistoryReviews] = useState<HumanReview[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending')
  const [selectedReview, setSelectedReview] = useState<HumanReview | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [modifiedOutput, setModifiedOutput] = useState('')
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    loadReviews()
  }, [childId])

  const loadReviews = async () => {
    setLoading(true)
    try {
      const [pending, all] = await Promise.all([
        getPendingReviews(childId),
        getAllReviews(childId),
      ])
      setReviews(pending)
      setHistoryReviews(all)
    } catch (e) {
      console.error('Onay yükleme hatası:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleReviewAction = async (
    reviewId: number,
    status: 'approved' | 'rejected' | 'modified'
  ) => {
    setUpdating(true)
    try {
      await updateReview(
        reviewId,
        status,
        reviewNotes || undefined,
        status === 'modified' ? modifiedOutput || undefined : undefined,
      )
      setSelectedReview(null)
      setReviewNotes('')
      setModifiedOutput('')
      await loadReviews()
    } catch (e) {
      console.error('Onay güncelleme hatası:', e)
    } finally {
      setUpdating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string; color: string; label: string }> = {
      pending: { bg: '#FEF3C7', color: '#92400E', label: '⏳ Bekliyor' },
      approved: { bg: '#D1FAE5', color: '#065F46', label: '✅ Onaylandı' },
      rejected: { bg: '#FEE2E2', color: '#991B1B', label: '❌ Reddedildi' },
      modified: { bg: '#DBEAFE', color: '#1E40AF', label: '✏️ Düzenlendi' },
    }
    const s = styles[status] || styles.pending
    return (
      <span style={{
        padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
        background: s.bg, color: s.color,
      }}>
        {s.label}
      </span>
    )
  }

  const getConfidenceBadge = (score?: number) => {
    if (score == null) return null
    const pct = Math.round(score * 100)
    const color = pct >= 70 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#EF4444'
    return (
      <span style={{
        padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
        background: `${color}15`, color,
      }}>
        🎯 Güven: {pct}%
      </span>
    )
  }

  const getTaskLabel = (taskType: string) => {
    const labels: Record<string, string> = {
      report: '📊 Haftalık Rapor',
      anomaly: '⚠️ Anomali Tespiti',
      analysis: '🔬 Davranış Analizi',
      deep_analysis: '📈 Derin Analiz',
      literature_review: '📚 Literatür Araştırması',
      parent_support: '💛 Ebeveyn Desteği',
      chat: '💬 Sohbet',
    }
    return labels[taskType] || taskType
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: '#64748B' }}>
        Onay kayıtları yükleniyor...
      </div>
    )
  }

  return (
    <div>
      {/* Tab Başlıkları */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        <button
          onClick={() => setActiveTab('pending')}
          style={{
            padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
            fontWeight: 600, fontSize: 13, transition: 'all 0.2s',
            background: activeTab === 'pending' ? '#0E7490' : '#E2E8F0',
            color: activeTab === 'pending' ? 'white' : '#475569',
          }}
        >
          Onay Bekleyenler ({reviews.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          style={{
            padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
            fontWeight: 600, fontSize: 13, transition: 'all 0.2s',
            background: activeTab === 'history' ? '#0E7490' : '#E2E8F0',
            color: activeTab === 'history' ? 'white' : '#475569',
          }}
        >
          Geçmiş
        </button>
      </div>

      {/* Onay Bekleyenler */}
      {activeTab === 'pending' && (
        <div>
          {reviews.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: 40, borderRadius: 12,
              background: '#F0FDFA', border: '1px dashed #99F6E4',
            }}>
              <span style={{ fontSize: 36 }}>✅</span>
              <p style={{ color: '#0F766E', fontWeight: 600, marginTop: 12 }}>
                Bekleyen onay yok
              </p>
              <p style={{ color: '#5EEAD4', fontSize: 13 }}>
                Tüm AI çıktıları güncel
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {reviews.map(review => (
                <div
                  key={review.id}
                  style={{
                    padding: 16, borderRadius: 12,
                    background: 'white', border: '1px solid #E2E8F0',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{getTaskLabel(review.task_type)}</span>
                      {getStatusBadge(review.status)}
                      {getConfidenceBadge(review.confidence_score)}
                    </div>
                    <span style={{ fontSize: 11, color: '#94A3B8' }}>
                      {review.created_at ? new Date(review.created_at).toLocaleString('tr-TR') : ''}
                    </span>
                  </div>

                  <div style={{
                    padding: 12, borderRadius: 8, background: '#F8FAFC',
                    fontSize: 13, lineHeight: 1.6, maxHeight: 200, overflowY: 'auto',
                    whiteSpace: 'pre-wrap', marginBottom: 12,
                  }}>
                    {review.ai_output}
                  </div>

                  {selectedReview?.id === review.id ? (
                    <div>
                      <textarea
                        value={reviewNotes}
                        onChange={e => setReviewNotes(e.target.value)}
                        placeholder="Uzman notlarınız (isteğe bağlı)..."
                        style={{
                          width: '100%', padding: 10, borderRadius: 8, border: '1px solid #E2E8F0',
                          fontSize: 13, minHeight: 60, marginBottom: 8, resize: 'vertical',
                        }}
                      />
                      <textarea
                        value={modifiedOutput}
                        onChange={e => setModifiedOutput(e.target.value)}
                        placeholder="Düzenlenen çıktı (sadece düzenleme için)..."
                        style={{
                          width: '100%', padding: 10, borderRadius: 8, border: '1px solid #E2E8F0',
                          fontSize: 13, minHeight: 60, marginBottom: 8, resize: 'vertical',
                        }}
                      />
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          onClick={() => handleReviewAction(review.id, 'approved')}
                          disabled={updating}
                          style={{
                            padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: '#10B981', color: 'white', fontWeight: 600, fontSize: 13,
                          }}
                        >
                          ✅ Onayla
                        </button>
                        <button
                          onClick={() => handleReviewAction(review.id, 'modified')}
                          disabled={updating || !modifiedOutput.trim()}
                          style={{
                            padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: '#3B82F6', color: 'white', fontWeight: 600, fontSize: 13,
                            opacity: modifiedOutput.trim() ? 1 : 0.5,
                          }}
                        >
                          ✏️ Düzenle & Onayla
                        </button>
                        <button
                          onClick={() => handleReviewAction(review.id, 'rejected')}
                          disabled={updating}
                          style={{
                            padding: '8px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: '#EF4444', color: 'white', fontWeight: 600, fontSize: 13,
                          }}
                        >
                          ❌ Reddet
                        </button>
                        <button
                          onClick={() => { setSelectedReview(null); setReviewNotes(''); setModifiedOutput('') }}
                          style={{
                            padding: '8px 16px', borderRadius: 8, border: '1px solid #E2E8F0',
                            background: 'white', color: '#64748B', cursor: 'pointer', fontSize: 13,
                          }}
                        >
                          İptal
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setSelectedReview(review)}
                      style={{
                        padding: '8px 16px', borderRadius: 8, border: '1px solid #0E7490',
                        background: 'transparent', color: '#0E7490', cursor: 'pointer',
                        fontWeight: 600, fontSize: 13,
                      }}
                    >
                      👤 Gözden Geçir
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Geçmiş */}
      {activeTab === 'history' && (
        <div>
          {historyReviews.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#94A3B8' }}>
              Henüz onay kaydı yok
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {historyReviews.map(review => (
                <div
                  key={review.id}
                  style={{
                    padding: 12, borderRadius: 10,
                    background: 'white', border: '1px solid #F1F5F9',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}
                >
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ fontSize: 13 }}>{getTaskLabel(review.task_type)}</span>
                    {getStatusBadge(review.status)}
                    {getConfidenceBadge(review.confidence_score)}
                  </div>
                  <div style={{ fontSize: 11, color: '#94A3B8' }}>
                    {review.reviewed_at
                      ? `Gözden geçirildi: ${new Date(review.reviewed_at).toLocaleString('tr-TR')}`
                      : review.created_at
                        ? new Date(review.created_at).toLocaleString('tr-TR')
                        : ''
                    }
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
