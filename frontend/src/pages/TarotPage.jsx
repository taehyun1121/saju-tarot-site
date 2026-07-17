import { useState, useEffect, useRef } from 'react'
import { API } from '../api'

// 질문 유형 6종 — 의미 맞는 RWS 메이저카드(퍼블릭도메인) 이미지 (public/type-cards/)
const QUESTION_TYPES = [
  { id: 'love',     label: '연애·짝사랑', img: '/type-cards/lovers.jpg',     ph: '예: 지금 이 사람과 잘 될 수 있을까요?' },
  { id: 'relation', label: '관계·궁합',   img: '/type-cards/temperance.jpg', ph: '예: 우리 두 사람 관계가 어떻게 흘러갈까요?' },
  { id: 'career',   label: '진로·직업',   img: '/type-cards/magician.jpg',   ph: '예: 지금 이직·도전, 시기가 맞을까요?' },
  { id: 'money',    label: '금전·재물',   img: '/type-cards/sun.jpg',        ph: '예: 재정 상황이 언제쯤 풀릴까요?' },
  { id: 'health',   label: '건강',        img: '/type-cards/strength.jpg',   ph: '예: 요즘 건강·컨디션 흐름이 궁금해요.' },
  { id: 'year',     label: '올해 종합운', img: '/type-cards/wheel.jpg',      ph: '예: 올 한 해 전체 흐름이 어떻게 될까요?' },
]

function SajuSummaryPanel({ sajuContext }) {
  const [open, setOpen] = useState(false)
  const [openItems, setOpenItems] = useState({})
  if (!sajuContext?.reading) return null
  const toggleItem = i => setOpenItems(p => ({ ...p, [i]: !p[i] }))
  const name = sajuContext.personName || null

  return (
    <div className="bg-app-card border border-p-600 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-app-dark transition-colors"
      >
        <span className="text-p-50 text-sm font-bold">
          🔮 {name ? `${name}의 사주풀이` : '사주풀이 결과'} 보기
          <span className="text-p-350 font-normal ml-2 text-xs">({sajuContext.pillars?.day?.hanja} 일주 / {sajuContext.ilgan} 일간)</span>
        </span>
        <span className="text-p-350 text-xs">{open ? '▲ 접기' : '▼ 펼치기'}</span>
      </button>

      {open && (
        <div className="border-t border-p-700 px-5 py-4 flex flex-col gap-3">
          {/* 사주 기둥 */}
          <div className="flex gap-2 flex-wrap">
            {['year','month','day','hour'].map(k => (
              sajuContext.pillars[k] ? (
                <div key={k} className={`flex-1 min-w-[58px] bg-app-input border rounded-xl py-3 px-1 text-center ${k==='day'?'border-gold':'border-p-600'}`}>
                  <div className="text-p-200 text-xs mb-1">{k==='year'?'년주':k==='month'?'월주':k==='day'?'일주':'시주'}</div>
                  <div className="text-p-10 text-xl tracking-widest mb-1">{sajuContext.pillars[k].hanja}</div>
                  <div className="text-p-150 text-xs">{sajuContext.pillars[k].korean}</div>
                </div>
              ) : null
            ))}
          </div>
          {/* 14항목 */}
          <div className="flex flex-col gap-1.5">
            {sajuContext.reading.map((item, i) => (
              <div key={i} className="border border-p-700 rounded-lg overflow-hidden">
                <button onClick={() => toggleItem(i)}
                  className="w-full flex items-center gap-2.5 bg-app-input hover:bg-[#15102a] px-3.5 py-2.5 text-left transition-colors">
                  <span className="w-5 h-5 bg-p-400 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0">{i+1}</span>
                  <span className="flex-1 text-p-10 text-sm">{item.title}</span>
                  <span className="text-p-350 text-xs">{openItems[i] ? '▲' : '▼'}</span>
                </button>
                {openItems[i] && (
                  <div className="px-3.5 py-3 bg-app-dark text-p-100 text-sm leading-relaxed border-t border-p-700">{item.content}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function TarotPage({ sajuContext, onSaveTarot, onSaveNewTarot }) {
  const [spreads, setSpreads] = useState([])
  const [useSaju, setUseSaju] = useState(false)
  const [typeId, setTypeId] = useState(null)
  const [question, setQuestion] = useState('')
  const [spreadId, setSpreadId] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/spreads`).then(r => r.json()).then(setSpreads)
  }, [])

  useEffect(() => {
    if (sajuContext) setUseSaju(true)
  }, [sajuContext])

  const selectedType = QUESTION_TYPES.find(t => t.id === typeId)

  const handleDraw = async () => {
    if (!spreadId) return
    setLoading(true); setResult(null)
    try {
      const res = await fetch(`${API}/tarot/draw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spread_id: spreadId,
          question: question.trim() || (selectedType ? `${selectedType.label} 전반` : ''),
          saju_context: useSaju && sajuContext ? sajuContext : null,
        })
      })
      const data = await res.json()
      setLoading(false); setResult(data)

      if (sajuContext?.historyId && onSaveTarot) {
        onSaveTarot(sajuContext.historyId, data)
      } else if (onSaveNewTarot) {
        onSaveNewTarot({ id: `${Date.now()}_tarot`, timestamp: new Date().toISOString(), type: 'tarot', person: null, saju: null, tarot: data })
      }
    } catch {
      setLoading(false)
      alert('서버 연결 오류')
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* 사주 결과 다시 보기 패널 */}
      {sajuContext && sajuContext.type !== 'compat' && (
        <SajuSummaryPanel sajuContext={sajuContext} />
      )}

      {/* 사주 연동 배너 */}
      {sajuContext && (
        <div className={`border rounded-lg px-4 py-3 max-w-[680px] mx-auto w-full ${sajuContext.type === 'compat' ? 'bg-[#1a102a] border-[#7040b0]' : 'bg-[#1a102a] border-[#5a3080]'}`}>
          <label className={`flex items-center gap-2.5 text-sm cursor-pointer ${sajuContext.type === 'compat' ? 'text-[#c080ff]' : 'text-p-50'}`}>
            <input type="checkbox" checked={useSaju}
              onChange={e => setUseSaju(e.target.checked)}
              className="w-4 h-4 accent-p-300" />
            <span>
              {sajuContext.type === 'compat' ? (
                <>💫 궁합 타로 연동 — <span className="text-gold font-bold">{sajuContext.person1Name || sajuContext.person1.pillars.day.hanja}</span> × <span className="text-gold font-bold">{sajuContext.person2Name || sajuContext.person2.pillars.day.hanja}</span></>
              ) : (
                <>{sajuContext.personName ? <><span className="text-gold font-bold">{sajuContext.personName}</span> 사주 연동</> : '사주 맥락 연동'}<span className="text-p-350 text-xs ml-2">({sajuContext.pillars.day.hanja} 일주 / 일간: {sajuContext.ilgan})</span></>
              )}
            </span>
          </label>
        </div>
      )}

      {/* 본문 — SajuPage와 동일 폭(max-w-680) */}
      <div className="max-w-[680px] mx-auto w-full flex flex-col gap-5">
        {/* 질문 유형 캐러셀 (가로 드래그·center-focus 확대) */}
        <TypeCarousel typeId={typeId}
          onSelect={id => { setTypeId(id); setQuestion(''); setSpreadId(''); setResult(null) }} />

        {/* 유형 선택 후 리딩 패널 */}
        {selectedType && (
          <div className="bg-app-card border border-p-600 rounded-2xl p-5 max-sm:p-4 flex flex-col gap-5">
            <div className="flex items-center gap-2.5">
              <img src={selectedType.img} alt="" className="w-9 h-12 rounded object-cover border border-p-500 shrink-0" />
              <h2 className="text-gold text-base font-bold">{selectedType.label} 타로</h2>
            </div>

            {/* 질문 입력 (텍스트영역, 높이 ↑) */}
            <div className="flex flex-col gap-1.5">
              <label className="text-p-200 text-sm">질문 입력 (선택)</label>
              <textarea rows={3} placeholder={selectedType.ph}
                value={question} onChange={e => setQuestion(e.target.value)}
                className="bg-app-input border border-p-600 rounded-[10px] px-[14px] py-3 min-h-[96px] text-p-10 text-sm outline-none focus:border-p-300 placeholder:text-[#4a3870] w-full resize-none leading-relaxed" />
            </div>

            {/* 배열법 선택 */}
            <div>
              <label className="block text-p-200 text-sm mb-2.5">배열법 선택</label>
              <div className="grid gap-2.5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))' }}>
                {spreads.map(s => (
                  <button key={s.id} onClick={() => setSpreadId(s.id)}
                    className={`border rounded-xl p-4 text-left flex flex-col gap-1.5 transition-all hover:border-p-400
                      ${spreadId === s.id ? 'border-gold bg-app-hover' : 'border-p-700 bg-app-input'}`}>
                    <span className="text-p-10 text-base font-bold">{s.name}</span>
                    <span className="text-gold text-sm font-semibold">{s.cards}장</span>
                    <span className="text-p-350 text-sm leading-snug">{s.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 뽑기 */}
            <button onClick={handleDraw} disabled={!spreadId || loading}
              className="w-full bg-gradient-to-br from-p-400 to-p-300 text-white py-3.5 rounded-lg font-bold text-base tracking-wide hover:opacity-85 disabled:opacity-50 transition-opacity">
              {loading ? '카드 뽑는 중...' : '✨ 카드 뽑기'}
            </button>
          </div>
        )}

        {/* 결과 */}
        {result && (
          <div className="bg-app-card border border-p-600 rounded-2xl overflow-hidden">
            <TarotResult result={result} />
          </div>
        )}
      </div>
    </div>
  )
}

/* ── 질문 유형 가로 캐러셀 (드래그 스크롤 · center-focus 확대) ── */
function TypeCarousel({ typeId, onSelect }) {
  const ref = useRef(null)
  const [scales, setScales] = useState({})
  const drag = useRef({ down: false, startX: 0, startScroll: 0, moved: false })

  const update = () => {
    const el = ref.current; if (!el) return
    const center = el.scrollLeft + el.clientWidth / 2
    const next = {}
    ;[...el.children].forEach((c, i) => {
      const cc = c.offsetLeft + c.offsetWidth / 2
      const norm = Math.min(Math.abs(cc - center) / (el.clientWidth / 2), 1)
      next[i] = 1.14 - norm * 0.44   // 정중앙 1.14(확대 팝업) → 가장자리 0.70
    })
    setScales(next)
  }

  useEffect(() => {
    update()
    const el = ref.current; let raf
    const onScroll = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(update) }
    el?.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', update)
    return () => { el?.removeEventListener('scroll', onScroll); window.removeEventListener('resize', update) }
  }, [])

  const centerOn = (i, behavior = 'smooth') => {
    const el = ref.current; if (!el) return
    const c = el.children[i]
    el.scrollTo({ left: c.offsetLeft + c.offsetWidth / 2 - el.clientWidth / 2, behavior })
  }

  const snap = () => {
    const el = ref.current; if (!el) return
    const center = el.scrollLeft + el.clientWidth / 2
    let best = 0, bd = Infinity
    ;[...el.children].forEach((c, i) => {
      const d = Math.abs(c.offsetLeft + c.offsetWidth / 2 - center)
      if (d < bd) { bd = d; best = i }
    })
    centerOn(best)
  }

  const down = e => { const el = ref.current; drag.current = { down: true, startX: e.clientX, startScroll: el.scrollLeft, moved: false } }
  const move = e => {
    if (!drag.current.down) return
    const el = ref.current, dx = e.clientX - drag.current.startX
    if (Math.abs(dx) > 4) drag.current.moved = true
    el.scrollLeft = drag.current.startScroll - dx
  }
  const up = () => { if (!drag.current.down) return; drag.current.down = false; snap() }

  const pick = (i, id) => { if (drag.current.moved) return; onSelect(id); centerOn(i) }

  return (
    <div className="flex flex-col gap-1">
      <p className="text-p-100 text-sm text-center font-bold">어떤 걸 물어볼까요?</p>
      <p className="text-p-350 text-xs text-center mb-1">← 좌우로 밀어 유형을 고르세요 →</p>
      <div ref={ref}
        onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerLeave={up}
        className="flex gap-5 overflow-x-auto py-10 items-center cursor-grab active:cursor-grabbing [&::-webkit-scrollbar]:hidden"
        style={{ scrollSnapType: 'x mandatory', scrollbarWidth: 'none', paddingLeft: 'calc(50% - 84px)', paddingRight: 'calc(50% - 84px)' }}>
        {QUESTION_TYPES.map((t, i) => {
          const sc = scales[i] ?? (t.id === typeId ? 1.14 : 0.72)
          const focused = sc > 1.02
          return (
            <button key={t.id} onClick={() => pick(i, t.id)} className="shrink-0 select-none"
              style={{ scrollSnapAlign: 'center', width: '168px', transformOrigin: 'center center', transform: `scale(${sc})`, transition: drag.current.down ? 'none' : 'transform .18s ease-out', zIndex: focused ? 5 : 1 }}>
              <div className={`rounded-2xl overflow-hidden border-2 transition-shadow ${typeId === t.id ? 'border-gold shadow-2xl shadow-[#00000066]' : 'border-p-600 shadow-lg'} bg-app-input`}>
                <img src={t.img} alt={t.label} draggable="false" className="w-full h-[252px] object-cover pointer-events-none" />
              </div>
              <p className={`text-center mt-3 text-lg font-bold ${typeId === t.id ? 'text-gold' : 'text-p-100'}`}>{t.label}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

/* ── 타로 결과 ── */
function TarotResult({ result }) {
  const [flipped, setFlipped] = useState({})
  const flipCard = i => setFlipped(prev => ({ ...prev, [i]: true }))
  const flipAll = () => {
    const all = {}
    result.cards.forEach((_, i) => all[i] = true)
    setFlipped(all)
  }

  const flippedCount = Object.values(flipped).filter(Boolean).length

  return (
    <div className="border-t border-p-600">
      {/* 결과 헤더 */}
      <div className="flex items-center gap-3 flex-wrap px-5 py-4 bg-app-dark border-b border-p-700">
        <span className="text-gold font-bold">{result.spread_name}</span>
        {result.question && <span className="text-p-50 italic text-sm flex-1">"{result.question}"</span>}
        <button onClick={flipAll}
          className="bg-p-750 border border-p-500 text-p-100 px-3 py-1.5 rounded-md text-sm hover:bg-p-700 transition-colors shrink-0">
          모두 공개
        </button>
      </div>

      {/* 카드 그리드 */}
      <div className="px-5 py-4">
        <SpreadLayout cards={result.cards} gridCols={result.grid_cols} gridRows={result.grid_rows}
          flipped={flipped} onFlip={flipCard} />
      </div>

      {/* 카드별 해석 */}
      {flippedCount > 0 && (
        <div className="px-5 pb-4 flex flex-col gap-3">
          <h4 className="text-p-50 text-sm font-bold">📖 카드별 해석</h4>
          {result.cards.map((card, i) => (
            flipped[i] && (
              <CardReading key={i} card={card} index={i} />
            )
          ))}
        </div>
      )}

      {/* 전체 종합 해석 */}
      {flippedCount === result.cards.length && result.overall_summary && (
        <OverallSummary text={result.overall_summary} />
      )}
    </div>
  )
}

/* ── 전체 종합 해석 (3단계 파싱) ── */
const SUMMARY_SECTIONS = [
  { sym: '①', label: '위치별 흐름', icon: '📍', color: 'border-[#5060c0] text-[#a0b0ff]' },
  { sym: '②', label: '카드 간 연결', icon: '🔗', color: 'border-[#705090] text-[#c0a0ff]' },
  { sym: '③', label: '종합 결론',   icon: '🌟', color: 'border-[#907030] text-[#ffd070]' },
]

function parseSummary(text) {
  const idxs = SUMMARY_SECTIONS.map(s => ({ ...s, idx: text.indexOf(s.sym) })).filter(s => s.idx !== -1)
  if (idxs.length === 0) return [{ label: null, icon: '🌟', color: 'border-[#5040a0] text-[#c0a0ff]', content: text }]

  return idxs.map((s, i) => {
    const start = s.idx + s.sym.length
    const end = idxs[i + 1] ? idxs[i + 1].idx : text.length
    return { label: s.label, icon: s.icon, color: s.color, content: text.slice(start, end).trim() }
  })
}

function SummarySection({ icon, label, color, content }) {
  const sentences = content.split(/(?<=[.。!?!?])\s+/).filter(Boolean)
  return (
    <div className={`border-l-[3px] pl-4 py-1 ${color.split(' ')[0]}`}>
      {label && (
        <p className={`text-xs font-bold mb-2 ${color.split(' ')[1]}`}>{icon} {label}</p>
      )}
      <div className="flex flex-col gap-1.5">
        {sentences.length > 1
          ? sentences.map((s, i) => <p key={i} className="text-p-100 text-sm leading-relaxed">{s}</p>)
          : <p className="text-p-100 text-sm leading-relaxed">{content}</p>
        }
      </div>
    </div>
  )
}

function OverallSummary({ text }) {
  const sections = parseSummary(text)
  return (
    <div className="mx-5 mb-5 bg-[#1a1238] border border-[#5040a0] rounded-xl p-4 flex flex-col gap-4">
      <h4 className="text-[#c0a0ff] text-sm font-bold">🌟 전체 종합 해석</h4>
      {sections.map((s, i) => (
        <SummarySection key={i} {...s} />
      ))}
    </div>
  )
}

/* ── 카드 1장 해석 ── */
function CardReading({ card }) {
  const [showStatic, setShowStatic] = useState(false)
  const [showSaju, setShowSaju] = useState(false)

  const hasAI = !!card.ai_reading

  return (
    <div className="bg-app-input border border-p-700 rounded-xl overflow-hidden">
      {/* 카드 헤더 */}
      <div className="flex items-center gap-2.5 px-4 py-3 bg-app-dark border-b border-p-700 flex-wrap">
        <span className="w-6 h-6 bg-p-400 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0">
          {card.position_num}
        </span>
        <span className="font-bold text-p-10">{card.position_name}</span>
        <span className="text-xs text-p-350 max-sm:hidden">{card.position_desc}</span>
        <span className={`ml-auto text-sm font-bold ${card.reversed ? 'text-[#e08080]' : 'text-gold'}`}>
          {card.card_name} {card.reversed ? '↺역' : '↑정'}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-3">
        <p className="text-p-350 text-xs sm:hidden">{card.position_desc}</p>

        {/* 키워드 */}
        <div className="flex items-center gap-2">
          <span className="text-p-350 text-xs">키워드</span>
          <span className={`text-sm font-bold px-2 py-0.5 rounded-md border text-xs
            ${card.reversed ? 'bg-[#2a1020] border-[#a04060] text-[#e08080]' : 'bg-[#1a2810] border-[#406020] text-[#a0d060]'}`}>
            {card.keyword}
          </span>
        </div>

        {/* AI 해석 (우선) 또는 정적 해석 */}
        {hasAI ? (
          <div className="flex flex-col gap-2">
            <div className="bg-app-dark rounded-lg px-4 py-3 border-l-[3px] border-p-400">
              <p className="text-p-100 text-sm leading-relaxed">{card.ai_reading}</p>
            </div>
            {/* AI 사주 인사이트 */}
            {card.ai_saju_insight && (
              <div className="bg-[#1a1030] rounded-lg px-4 py-3 border-l-[3px] border-[#7040b0]">
                <p className="text-[#c0a0e0] text-xs text-p-350 mb-1">🔮 사주 연동</p>
                <p className="text-[#c0a0e0] text-sm leading-relaxed">{card.ai_saju_insight}</p>
              </div>
            )}
            {/* 기본 해석 접어두기 */}
            <button onClick={() => setShowStatic(v => !v)}
              className="self-start text-xs text-p-350 hover:text-p-200 transition-colors">
              {showStatic ? '▲ 기본 해석 접기' : '▼ 기본 해석 보기'}
            </button>
            {showStatic && (
              <div className="bg-app-dark rounded-lg px-4 py-3 border-l-[3px] border-p-600 opacity-70">
                <p className="text-p-150 text-sm leading-relaxed">{card.meaning}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="bg-app-dark rounded-lg px-4 py-3 border-l-[3px] border-p-400">
              <p className="text-p-100 text-sm leading-relaxed">{card.meaning}</p>
            </div>
            {card.saju_meaning && (
              <div>
                <button onClick={() => setShowSaju(v => !v)}
                  className="flex items-center gap-1.5 text-xs text-[#a080d0] hover:text-[#c0a0f0] transition-colors">
                  <span>🔮 사주 연동 해석</span>
                  <span>{showSaju ? '▲' : '▼'}</span>
                </button>
                {showSaju && (
                  <div className="mt-2 bg-[#1a1030] rounded-lg px-4 py-3 border-l-[3px] border-[#7040b0]">
                    <p className="text-[#c0a0e0] text-sm leading-relaxed">{card.saju_meaning}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── 스프레드 레이아웃 ── */
function SpreadLayout({ cards, gridCols, gridRows, flipped, onFlip }) {
  const grid = {}
  cards.forEach((card, i) => {
    const key = `${card.row}-${card.col}`
    if (!grid[key]) grid[key] = []
    grid[key].push({ card, idx: i })
  })
  const cellW = 100, cellH = 160, gap = 12
  return (
    <div className="overflow-x-auto">
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${gridCols}, ${cellW}px)`,
        gridTemplateRows: `repeat(${gridRows}, ${cellH}px)`,
        gap: `${gap}px`,
        justifyContent: 'center',
        margin: '0 auto 8px',
      }}>
        {Array.from({ length: gridRows }, (_, r) =>
          Array.from({ length: gridCols }, (_, c) => {
            const key = `${r}-${c}`
            const items = grid[key] || []
            if (items.length === 0) return <div key={key} />
            return (
              <div key={key} style={{ position: 'relative', gridColumn: c+1, gridRow: r+1 }}>
                {items.map(({ card, idx }) => (
                  <CardSlot key={idx} card={card}
                    flipped={!!flipped[idx]} onFlip={() => onFlip(idx)}
                    isCross={card.cross} />
                ))}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

function CardSlot({ card, flipped, onFlip, isCross }) {
  return (
    <div
      className={`w-[100px] h-[160px] rounded-lg overflow-hidden transition-transform
        ${!flipped ? 'cursor-pointer hover:-translate-y-1' : ''}
        ${isCross ? 'cursor-default' : ''}`}
      onClick={!flipped ? onFlip : undefined}
      style={isCross ? {
        position: 'absolute', transform: 'rotate(90deg)',
        transformOrigin: 'center center',
        top: '50%', left: '50%', marginTop: '-50px', marginLeft: '-80px', zIndex: 2,
      } : {}}
    >
      {!flipped ? (
        <div className="w-full h-full bg-gradient-to-br from-p-800 to-p-900 border-2 border-p-400 rounded-lg flex flex-col items-center justify-center gap-1.5">
          <span className="text-3xl">🔮</span>
          <span className="text-lg font-bold text-gold">{card.position_num}</span>
          <span className="text-xs text-p-350 text-center leading-tight px-1">{card.position_name}</span>
        </div>
      ) : (
        <div className={`w-full h-full relative border-2 rounded-lg overflow-hidden
          ${card.reversed ? 'border-[#a04060]' : 'border-p-400'}`}>
          <div className="absolute top-0 left-0 right-0 flex justify-between px-1.5 py-0.5 z-10 bg-black/60">
            <span className="w-[18px] h-[18px] bg-p-400 rounded-full flex items-center justify-center text-[0.6rem] font-bold text-white">
              {card.position_num}
            </span>
            <span className="text-[0.6rem] text-gold">{card.reversed ? '↺역' : '↑정'}</span>
          </div>
          <img src={card.image} alt={card.card_name}
            className="w-full h-[136px] object-cover block"
            style={card.reversed ? { transform: 'rotate(180deg)' } : {}} />
          <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-1.5 py-0.5">
            <span className="text-[0.65rem] text-p-10">{card.card_name}</span>
          </div>
        </div>
      )}
    </div>
  )
}
