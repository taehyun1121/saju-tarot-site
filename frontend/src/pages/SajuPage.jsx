import { useState } from 'react'
import './SajuPage.css'

const HOUR_OPTIONS = [
  { value: '', label: '모름' },
  ...Array.from({length: 24}, (_, i) => ({ value: i, label: `${i}시` }))
]

export default function SajuPage({ onGoToTarot }) {
  const [form, setForm] = useState({ year:'', month:'', day:'', hour:'', gender:'남' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [openItems, setOpenItems] = useState({})

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.year || !form.month || !form.day) { setError('년/월/일은 필수입니다'); return }
    setLoading(true)
    try {
      const res = await fetch('/api/saju', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: Number(form.year), month: Number(form.month),
          day: Number(form.day),
          hour: form.hour !== '' ? Number(form.hour) : null,
          gender: form.gender
        })
      })
      const data = await res.json()
      setResult(data)
      setOpenItems({})
    } catch(e) { setError('서버 연결 오류') }
    setLoading(false)
  }

  const toggle = (i) => setOpenItems(prev => ({ ...prev, [i]: !prev[i] }))

  return (
    <div className="saju-page">
      <div className="saju-form-card">
        <h2 className="section-title">🔮 사주풀이</h2>
        <form onSubmit={handleSubmit} className="saju-form">
          <div className="form-row">
            <div className="form-group">
              <label>태어난 년도</label>
              <input type="number" placeholder="예: 1990" min="1900" max="2025"
                value={form.year} onChange={e => setForm({...form, year: e.target.value})} />
            </div>
            <div className="form-group">
              <label>월</label>
              <input type="number" placeholder="예: 3" min="1" max="12"
                value={form.month} onChange={e => setForm({...form, month: e.target.value})} />
            </div>
            <div className="form-group">
              <label>일</label>
              <input type="number" placeholder="예: 15" min="1" max="31"
                value={form.day} onChange={e => setForm({...form, day: e.target.value})} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>태어난 시간</label>
              <select value={form.hour} onChange={e => setForm({...form, hour: e.target.value})}>
                {HOUR_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>성별</label>
              <div className="gender-btns">
                <button type="button" className={`gender-btn ${form.gender==='남'?'active':''}`}
                  onClick={() => setForm({...form, gender:'남'})}>남성</button>
                <button type="button" className={`gender-btn ${form.gender==='여'?'active':''}`}
                  onClick={() => setForm({...form, gender:'여'})}>여성</button>
              </div>
            </div>
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? '계산 중...' : '사주풀이 보기'}
          </button>
        </form>
      </div>

      {result && (
        <div className="saju-result">
          {/* 사주 기둥 */}
          <div className="pillars-card">
            <h3>만세력</h3>
            <div className="pillars">
              {['year','month','day','hour'].map(k => (
                result.pillars[k] ? (
                  <div key={k} className={`pillar ${k === 'day' ? 'day-pillar' : ''}`}>
                    <div className="pillar-label">
                      {k==='year'?'년주':k==='month'?'월주':k==='day'?'일주':'시주'}
                    </div>
                    <div className="pillar-hanja">{result.pillars[k].hanja}</div>
                    <div className="pillar-korean">{result.pillars[k].korean}</div>
                  </div>
                ) : (
                  <div key={k} className="pillar pillar-unknown">
                    <div className="pillar-label">시주</div>
                    <div className="pillar-hanja">??</div>
                    <div className="pillar-korean">모름</div>
                  </div>
                )
              ))}
            </div>
            <div className="daeun-row">
              <span className="info-label">현재 대운</span>
              {result.daeun.slice(0,6).map((d,i) => (
                <span key={i} className={`daeun-item ${i===2?'current-daeun':''}`}>
                  {d.hanja}<small>({d.start}~{d.end})</small>
                </span>
              ))}
            </div>
            <div className="seun-row">
              <span className="info-label">2026 세운</span>
              <span className="seun-value">{result.seun}</span>
            </div>
          </div>

          {/* 14항목 */}
          <div className="reading-card">
            <h3>14항목 풀이</h3>
            <div className="accordion">
              {result.reading.map((item, i) => (
                <div key={i} className={`accordion-item ${openItems[i]?'open':''}`}>
                  <button className="accordion-header" onClick={() => toggle(i)}>
                    <span className="item-num">{i+1}</span>
                    <span className="item-title">{item.title}</span>
                    <span className="arrow">{openItems[i]?'▲':'▼'}</span>
                  </button>
                  {openItems[i] && (
                    <div className="accordion-body">{item.content}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button className="tarot-link-btn" onClick={() => onGoToTarot(result)}>
            🃏 이 사주로 타로 보기 →
          </button>
        </div>
      )}
    </div>
  )
}
