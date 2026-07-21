import { useState, useEffect } from 'react'
import { API } from '../api'

// 1+1 오픈 이벤트 배너 — 백엔드 /api/promo가 단일 소스(종료시각 하드코딩 없음).
// 비활성/조회실패면 조용히 렌더 안 함(부가기능, 결제 흐름을 막으면 안 됨).
export default function PromoBanner({ className = '' }) {
  const [promo, setPromo] = useState(null)
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    let alive = true
    fetch(`${API}/promo`).then(r => r.json()).then(d => { if (alive) setPromo(d) }).catch(() => {})
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!promo?.active) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [promo])

  if (!promo?.active || !promo.ends_at) return null
  const remainMs = new Date(promo.ends_at).getTime() - now
  if (remainMs <= 0) return null
  const d = Math.floor(remainMs / 86400000)
  const h = Math.floor((remainMs % 86400000) / 3600000)
  const m = Math.floor((remainMs % 3600000) / 60000)

  return (
    <div className={`promobanner ${className}`}>
      <span className="pb-badge">1+1</span>
      <span className="pb-label">{promo.label}</span>
      <span className="pb-timer">종료까지 {d}일 {h}시간 {m}분</span>
    </div>
  )
}
