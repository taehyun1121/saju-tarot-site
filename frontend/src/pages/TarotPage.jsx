import { useState, useEffect } from 'react'

const API = '/api'
const MAX_QUESTIONS = 4

function newQuestion(id) {
  return { id, question: '', spreadId: '', result: null, loading: false }
}

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
  const [questions, setQuestions] = useState([newQuestion(1)])
  const [nextId, setNextId] = useState(2)

  useEffect(() => {
    fetch(`${API}/spreads`).then(r => r.json()).then(setSpreads)
  }, [])

  useEffect(() => {
    if (sajuContext) setUseSaju(true)
  }, [sajuContext])

  const updateQ = (id, patch) =>
    setQuestions(prev => prev.map(q => q.id === id ? { ...q, ...patch } : q))

  const addQuestion = () => {
    if (questions.length >= MAX_QUESTIONS) return
    setQuestions(prev => [...prev, newQuestion(nextId)])
    setNextId(n => n + 1)
  }

  const removeQuestion = (id) =>
    setQuestions(prev => prev.filter(q => q.id !== id))

  const handleDraw = async (qId) => {
    const q = questions.find(x => x.id === qId)
    if (!q?.spreadId) return
    updateQ(qId, { loading: true, result: null })
    try {
      const res = await fetch(`${API}/tarot/draw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spread_id: q.spreadId,
          question: q.question,
          saju_context: useSaju && sajuContext ? sajuContext : null,
        })
      })
      const data = await res.json()
      updateQ(qId, { loading: false, result: data })

      if (sajuContext?.historyId && onSaveTarot) {
        onSaveTarot(sajuContext.historyId, data)
      } else if (onSaveNewTarot) {
        onSaveNewTarot({ id: `${Date.now()}_tarot`, timestamp: new Date().toISOString(), type: 'tarot', person: null, saju: null, tarot: data })
      }
    } catch {
      updateQ(qId, { loading: false })
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
        <div className={`border rounded-lg px-4 py-3 ${sajuContext.type === 'compat' ? 'bg-[#1a102a] border-[#7040b0]' : 'bg-[#1a102a] border-[#5a3080]'}`}>
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

      {/* 질문 카드들 */}
      {questions.map((q, idx) => (
        <QuestionCard
          key={q.id}
          q={q}
          idx={idx}
          spreads={spreads}
          canRemove={questions.length > 1}
          onUpdate={patch => updateQ(q.id, patch)}
          onRemove={() => removeQuestion(q.id)}
          onDraw={() => handleDraw(q.id)}
        />
      ))}

      {/* 질문 추가 버튼 */}
      {questions.length < MAX_QUESTIONS && (
        <button onClick={addQuestion}
          className="w-full py-3 border border-dashed border-p-500 text-p-200 rounded-xl text-sm hover:border-p-300 hover:text-p-100 hover:bg-app-hover transition-all">
          + 질문 추가 ({questions.length}/{MAX_QUESTIONS})
        </button>
      )}
    </div>
  )
}

/* ── 질문 1개 카드 ── */
function QuestionCard({ q, idx, spreads, canRemove, onUpdate, onRemove, onDraw }) {
  return (
    <div className="bg-app-card border border-p-600 rounded-xl overflow-hidden">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-p-700 bg-app-dark">
        <h2 className="text-gold text-base font-bold">🃏 질문 {idx + 1}</h2>
        {canRemove && (
          <button onClick={onRemove}
            className="text-p-350 hover:text-[#e08080] text-xs border border-p-600 hover:border-[#c06060] px-2.5 py-1 rounded-md transition-colors">
            ✕ 삭제
          </button>
        )}
      </div>

      <div className="p-5 max-sm:p-4 flex flex-col gap-5">
        {/* 질문 입력 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-p-200 text-sm">질문 입력 (선택)</label>
          <input type="text" placeholder="예: 이 사람과의 관계가 어떻게 될까요?"
            value={q.question} onChange={e => onUpdate({ question: e.target.value })}
            className="bg-app-input border border-p-600 rounded-lg px-3 py-2.5 text-p-10 text-base outline-none focus:border-p-300 placeholder:text-[#4a3870]" />
        </div>

        {/* 배열법 선택 */}
        <div>
          <label className="block text-p-200 text-sm mb-2.5">배열법 선택</label>
          <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))' }}>
            {spreads.map(s => (
              <button key={s.id} onClick={() => onUpdate({ spreadId: s.id })}
                className={`border rounded-xl p-3 text-left flex flex-col gap-1 transition-all hover:border-p-400
                  ${q.spreadId === s.id ? 'border-gold bg-app-hover' : 'border-p-700 bg-app-input'}`}>
                <span className="text-p-10 text-sm font-bold">{s.name}</span>
                <span className="text-gold text-xs">{s.cards}장</span>
                <span className="text-p-350 text-xs leading-snug">{s.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 뽑기 버튼 */}
        <button onClick={onDraw} disabled={!q.spreadId || q.loading}
          className="w-full bg-gradient-to-br from-p-400 to-p-300 text-white py-3.5 rounded-lg font-bold text-base tracking-wide hover:opacity-85 disabled:opacity-50 transition-opacity">
          {q.loading ? '카드 뽑는 중...' : '✨ 카드 뽑기'}
        </button>
      </div>

      {/* 결과 */}
      {q.result && <TarotResult result={q.result} />}
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
        <div className="mx-5 mb-5 bg-[#1a1238] border border-[#5040a0] rounded-xl p-4">
          <h4 className="text-[#c0a0ff] text-sm font-bold mb-2">🌟 전체 종합 해석</h4>
          <p className="text-p-100 text-sm leading-relaxed">{result.overall_summary}</p>
        </div>
      )}
    </div>
  )
}

/* ── 카드 1장 해석 ── */
function CardReading({ card }) {
  const [showSaju, setShowSaju] = useState(false)
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
        {/* 포지션 설명 (모바일용) */}
        <p className="text-p-350 text-xs sm:hidden">{card.position_desc}</p>

        {/* 키워드 */}
        <div className="flex items-center gap-2">
          <span className="text-p-350 text-xs">키워드</span>
          <span className={`text-sm font-bold px-2 py-0.5 rounded-md border text-xs
            ${card.reversed ? 'bg-[#2a1020] border-[#a04060] text-[#e08080]' : 'bg-[#1a2810] border-[#406020] text-[#a0d060]'}`}>
            {card.keyword}
          </span>
        </div>

        {/* 포지션 해석 */}
        <div className="bg-app-dark rounded-lg px-4 py-3 border-l-[3px] border-p-400">
          <p className="text-p-100 text-sm leading-relaxed">{card.meaning}</p>
        </div>

        {/* 사주 연동 해석 */}
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
