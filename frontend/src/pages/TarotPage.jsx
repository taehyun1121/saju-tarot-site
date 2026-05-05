import { useState, useEffect } from 'react'
import './TarotPage.css'

const API = '/api'

export default function TarotPage({ sajuContext }) {
  const [spreads, setSpreads] = useState([])
  const [selectedSpread, setSelectedSpread] = useState('')
  const [question, setQuestion] = useState('')
  const [useSaju, setUseSaju] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [flipped, setFlipped] = useState({})

  useEffect(() => {
    fetch(`${API}/spreads`).then(r => r.json()).then(setSpreads)
  }, [])

  useEffect(() => {
    if (sajuContext) setUseSaju(true)
  }, [sajuContext])

  const handleDraw = async () => {
    if (!selectedSpread) return
    setLoading(true)
    setFlipped({})
    setResult(null)
    try {
      const res = await fetch(`${API}/tarot/draw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spread_id: selectedSpread,
          question,
          saju_context: useSaju && sajuContext ? sajuContext : null,
        })
      })
      const data = await res.json()
      setResult(data)
    } catch(e) { alert('서버 연결 오류') }
    setLoading(false)
  }

  const flipCard = (i) => setFlipped(prev => ({ ...prev, [i]: true }))
  const flipAll = () => {
    if (!result) return
    const all = {}
    result.cards.forEach((_, i) => all[i] = true)
    setFlipped(all)
  }

  return (
    <div className="tarot-page">
      {/* 스프레드 선택 */}
      <div className="tarot-setup-card">
        <h2 className="section-title">🃏 타로카드</h2>

        {sajuContext && (
          <div className="saju-context-banner">
            <label className="checkbox-label">
              <input type="checkbox" checked={useSaju}
                onChange={e => setUseSaju(e.target.checked)} />
              사주 맥락 연동 ({sajuContext.pillars.day.hanja} 일주 / 일간: {sajuContext.ilgan})
            </label>
          </div>
        )}

        <div className="form-group" style={{marginBottom:'16px'}}>
          <label>질문 입력 (선택)</label>
          <input type="text" placeholder="예: 이 사람과 재회할 수 있을까?"
            value={question} onChange={e => setQuestion(e.target.value)} />
        </div>

        <div className="spread-section">
          <label className="spread-label">배열법 선택</label>
          <div className="spread-grid">
            {spreads.map(s => (
              <button key={s.id}
                className={`spread-btn ${selectedSpread === s.id ? 'active' : ''}`}
                onClick={() => setSelectedSpread(s.id)}
              >
                <span className="spread-name">{s.name}</span>
                <span className="spread-cards">{s.cards}장</span>
                <span className="spread-desc">{s.description}</span>
              </button>
            ))}
          </div>
        </div>

        <button className="draw-btn" onClick={handleDraw}
          disabled={!selectedSpread || loading}>
          {loading ? '카드 뽑는 중...' : '✨ 카드 뽑기'}
        </button>
      </div>

      {/* 결과 */}
      {result && (
        <div className="tarot-result-card">
          <div className="result-header">
            <h3>{result.spread_name}</h3>
            {result.question && <p className="result-question">"{result.question}"</p>}
            <button className="flip-all-btn" onClick={flipAll}>모두 공개</button>
          </div>

          <SpreadLayout
            cards={result.cards}
            gridCols={result.grid_cols}
            gridRows={result.grid_rows}
            flipped={flipped}
            onFlip={flipCard}
          />

          {/* 카드 해석 목록 */}
          <div className="card-list">
            {result.cards.map((card, i) => (
              flipped[i] && (
                <div key={i} className="card-reading">
                  <div className="card-reading-header">
                    <span className="pos-badge">{card.position_num}</span>
                    <span className="pos-name">{card.position_name}</span>
                    <span className="card-name-small">
                      {card.card_name} {card.reversed ? '↺역' : '↑정'}
                    </span>
                  </div>
                  <p className="pos-desc">{card.position_desc}</p>
                  <p className="card-keyword">→ {card.keyword}</p>
                </div>
              )
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function SpreadLayout({ cards, gridCols, gridRows, flipped, onFlip }) {
  // 그리드 셀에 카드 배치
  const grid = {}
  cards.forEach((card, i) => {
    const key = `${card.row}-${card.col}`
    if (!grid[key]) grid[key] = []
    grid[key].push({ card, idx: i })
  })

  const cellW = 100, cellH = 160, gap = 12

  return (
    <div className="spread-layout" style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${gridCols}, ${cellW}px)`,
      gridTemplateRows: `repeat(${gridRows}, ${cellH}px)`,
      gap: `${gap}px`,
      justifyContent: 'center',
      margin: '20px auto',
    }}>
      {Array.from({length: gridRows}, (_, r) =>
        Array.from({length: gridCols}, (_, c) => {
          const key = `${r}-${c}`
          const items = grid[key] || []
          if (items.length === 0) return <div key={key} />

          return (
            <div key={key} style={{position:'relative', gridColumn: c+1, gridRow: r+1}}>
              {items.map(({card, idx}) => (
                <CardSlot key={idx} card={card} idx={idx}
                  flipped={!!flipped[idx]} onFlip={() => onFlip(idx)}
                  isCross={card.cross} />
              ))}
            </div>
          )
        })
      )}
    </div>
  )
}

function CardSlot({ card, idx, flipped, onFlip, isCross }) {
  return (
    <div
      className={`card-slot ${flipped ? 'flipped' : ''} ${isCross ? 'cross-card' : ''}`}
      onClick={!flipped ? onFlip : undefined}
      style={isCross ? {
        position: 'absolute',
        transform: 'rotate(90deg)',
        transformOrigin: 'center center',
        top: '50%', left: '50%',
        marginTop: '-50px', marginLeft: '-80px',
        zIndex: 2,
      } : {}}
    >
      {!flipped ? (
        <div className="card-back">
          <span>🔮</span>
          <span className="card-back-num">{card.position_num}</span>
          <span className="card-back-label">{card.position_name}</span>
        </div>
      ) : (
        <div className={`card-front ${card.reversed ? 'reversed' : ''}`}>
          <div className="card-top-bar">
            <span className="pos-num-badge">{card.position_num}</span>
            <span className="dir-badge">{card.reversed ? '↺역' : '↑정'}</span>
          </div>
          <img src={card.image} alt={card.card_name}
            className="card-img"
            style={card.reversed ? {transform:'rotate(180deg)'} : {}} />
          <div className="card-bottom">
            <span className="card-bottom-name">{card.card_name}</span>
          </div>
        </div>
      )}
    </div>
  )
}
