import { useState } from 'react'

function formatDate(iso) {
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function TypeBadge({ type }) {
  const map = {
    'saju':        'bg-[#2a3860] text-[#80b0ff] border border-[#3a4880]',
    'saju+tarot':  'bg-[#3a2060] text-[#c080ff] border border-[#5a3080]',
    'tarot':       'bg-[#382060] text-[#e0a0ff] border border-[#503070]',
    'compat':      'bg-[#3a1860] text-[#d080ff] border border-[#6a3080]',
    'compat+tarot':'bg-[#4a1070] text-[#e0a0ff] border border-[#7a30a0]',
  }
  const label = { 'saju':'사주', 'saju+tarot':'사주+타로', 'tarot':'타로', 'compat':'궁합', 'compat+tarot':'궁합+타로' }
  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-xl text-xs font-bold ${map[type] || ''}`}>
      {label[type] || type}
    </span>
  )
}

function PersonInfo({ person }) {
  if (!person) return null
  const hour = person.hour !== '' && person.hour != null ? ` ${person.hour}시` : ''
  return (
    <span className="text-p-150 text-sm max-sm:text-xs">
      {person.year}/{person.month}/{person.day}{hour} · {person.gender}성
    </span>
  )
}

function SajuDetail({ saju }) {
  const [openItems, setOpenItems] = useState({})
  const toggle = (i) => setOpenItems(prev => ({ ...prev, [i]: !prev[i] }))
  const allOpen = saju?.reading && Object.keys(openItems).length === saju.reading.length && Object.values(openItems).every(Boolean)
  const toggleAll = () => {
    if (allOpen) setOpenItems({})
    else setOpenItems(Object.fromEntries((saju?.reading || []).map((_, i) => [i, true])))
  }

  if (!saju?.pillars || !saju?.reading)
    return <p className="text-p-350 text-sm">데이터 오류 (저장 당시 서버 오류)</p>

  return (
    <div className="mb-6 last:mb-0">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-p-600">
        <h4 className="text-p-100 text-sm font-bold">🔮 사주풀이</h4>
        <button onClick={toggleAll} className="text-p-350 hover:text-p-100 text-xs transition-colors">
          {allOpen ? '전체 접기' : '전체 펼치기'}
        </button>
      </div>

      <div className="flex gap-1.5 mb-3 flex-wrap">
        {['year','month','day','hour'].map(k => (
          saju.pillars[k] ? (
            <div key={k} className={`flex-1 min-w-[52px] border rounded-lg py-2 px-1 text-center
              ${k==='day' ? 'border-gold bg-[#2a2010]' : 'border-p-600 bg-app-card'}`}>
              <div className="text-p-200 text-xs mb-1">{k==='year'?'년주':k==='month'?'월주':k==='day'?'일주':'시주'}</div>
              <div className="text-p-10 text-base font-bold max-sm:text-sm">{saju.pillars[k].hanja}</div>
              <div className="text-p-150 text-xs mt-0.5">{saju.pillars[k].korean}</div>
            </div>
          ) : (
            <div key={k} className="flex-1 min-w-[52px] border border-p-600 bg-app-card rounded-lg py-2 px-1 text-center opacity-40">
              <div className="text-p-200 text-xs mb-1">시주</div>
              <div className="text-p-600 text-base font-bold">??</div>
              <div className="text-p-150 text-xs mt-0.5">모름</div>
            </div>
          )
        ))}
      </div>

      <div className="flex items-center gap-2 flex-wrap mb-2 text-sm">
        <span className="text-p-200 text-xs min-w-[40px]">대운</span>
        {saju.daeun.slice(0,6).map((d,i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-md border
            ${i===2 ? 'border-gold text-gold' : 'border-p-600 text-p-100 bg-app-deep'}`}>
            {d.hanja}
            <small className="text-p-350 ml-0.5 text-[0.62rem] max-sm:hidden">({d.start}~{d.end})</small>
          </span>
        ))}
      </div>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-p-200 text-xs min-w-[60px]">2026 세운</span>
        <span className="text-gold font-bold">{saju.seun}</span>
      </div>

      <div className="border border-p-600 rounded-lg overflow-hidden">
        {saju.reading.map((item, i) => (
          <div key={i} className="border-b border-p-600 last:border-b-0">
            <button
              onClick={() => toggle(i)}
              className="w-full flex items-center gap-2.5 bg-app-dark hover:bg-[#2a2050] px-3 py-2.5 text-left transition-colors"
            >
              <span className="w-5 h-5 bg-p-600 rounded-full flex items-center justify-center text-xs text-p-50 shrink-0">{i+1}</span>
              <span className="flex-1 text-p-100 text-sm max-sm:text-xs">{item.title}</span>
              <span className="text-p-350 text-xs">{openItems[i] ? '▲' : '▼'}</span>
            </button>
            {openItems[i] && (
              <div className="px-3 py-3 bg-[#1a1238] text-p-100 text-sm leading-relaxed max-sm:text-xs">
                {item.content}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function CompatDetail({ compat }) {
  const [openItems, setOpenItems] = useState({})
  const toggle = i => setOpenItems(prev => ({ ...prev, [i]: !prev[i] }))
  if (!compat?.reading) return null
  return (
    <div className="mb-6 last:mb-0">
      <h4 className="text-[#c080ff] text-sm font-bold mb-3 pb-2 border-b border-p-600">
        💫 궁합 풀이 — {compat.person1?.pillars?.day?.hanja} × {compat.person2?.pillars?.day?.hanja}
      </h4>
      <div className="grid grid-cols-2 gap-2 mb-4">
        {[compat.person1, compat.person2].map((p, idx) => p && (
          <div key={idx} className="bg-app-dark border border-p-600 rounded-lg p-2.5">
            <div className="text-p-200 text-xs mb-1.5">대상{idx+1}</div>
            <div className="flex gap-1 flex-wrap">
              {['year','month','day'].map(k => p.pillars[k] && (
                <div key={k} className={`flex-1 min-w-[36px] border rounded py-1 px-0.5 text-center text-xs ${k==='day'?'border-gold':'border-p-600'}`}>
                  <div className="text-p-10 font-bold">{p.pillars[k].hanja}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="border border-p-600 rounded-lg overflow-hidden">
        {compat.reading.map((item, i) => (
          <div key={i} className="border-b border-p-600 last:border-b-0">
            <button onClick={() => toggle(i)}
              className="w-full flex items-center gap-2.5 bg-app-dark hover:bg-[#2a1060] px-3 py-2.5 text-left transition-colors">
              <span className="w-5 h-5 bg-[#5a3080] rounded-full flex items-center justify-center text-xs text-[#d0a0ff] shrink-0">{i+1}</span>
              <span className="flex-1 text-p-100 text-sm max-sm:text-xs">{item.title}</span>
              <span className="text-p-350 text-xs">{openItems[i] ? '▲' : '▼'}</span>
            </button>
            {openItems[i] && (
              <div className="px-3 py-3 bg-[#1a1238] text-p-100 text-sm leading-relaxed max-sm:text-xs">{item.content}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function TarotDetail({ tarot }) {
  return (
    <div className="mb-6 last:mb-0">
      <h4 className="text-p-100 text-sm font-bold mb-3 pb-2 border-b border-p-600">
        🃏 타로카드 — {tarot.spread_name}
      </h4>
      {tarot.question && (
        <p className="text-p-50 italic text-sm mb-3">"{tarot.question}"</p>
      )}
      <div className="flex flex-col gap-2.5">
        {tarot.cards.map((card, i) => (
          <div key={i} className="bg-app-dark border border-p-600 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="w-6 h-6 bg-p-600 rounded-full flex items-center justify-center text-xs font-bold text-p-50 shrink-0">
                {card.position_num}
              </span>
              <span className="text-p-200 text-sm font-bold">{card.position_name}</span>
              <span className="text-p-10 text-sm max-sm:w-full max-sm:ml-0 ml-auto">
                {card.card_name} {card.reversed ? '↺역' : '↑정'}
              </span>
            </div>
            <p className="text-p-350 text-xs mb-1">{card.position_desc}</p>
            <p className="text-[#c0a0ff] text-sm mb-1.5">→ {card.keyword}</p>
            <p className="text-p-100 text-sm leading-relaxed">{card.meaning}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function HistoryEntry({ entry }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className={`bg-[#1e1540] border rounded-xl overflow-hidden transition-colors
      ${expanded ? 'border-p-400' : 'border-p-600 hover:border-p-400'}`}>
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full px-4 py-3.5 flex justify-between items-center hover:bg-[#2a1e50] transition-colors"
      >
        <div className="flex items-center gap-2.5 flex-wrap">
          <TypeBadge type={entry.type} />
          <PersonInfo person={entry.person} />
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-2">
          <span className="text-p-350 text-xs max-sm:hidden">{formatDate(entry.timestamp)}</span>
          <span className="text-p-400 text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>
      {expanded && (
        <div className="border-t border-p-600 p-4 max-sm:p-3">
          <p className="text-p-350 text-xs mb-3 sm:hidden">{formatDate(entry.timestamp)}</p>
          {entry.compat && <CompatDetail compat={entry.compat} />}
          {entry.saju && <SajuDetail saju={entry.saju} />}
          {entry.tarot && <TarotDetail tarot={entry.tarot} />}
        </div>
      )}
    </div>
  )
}

export default function HistoryPage({ history, onClear }) {
  const [confirmClear, setConfirmClear] = useState(false)

  if (history.length === 0) {
    return (
      <div className="text-center py-20 text-p-150">
        <p className="text-lg mb-2">📋 아직 기록이 없습니다.</p>
        <p className="text-sm opacity-70">사주풀이나 타로카드를 보면 여기에 기록이 쌓입니다.</p>
      </div>
    )
  }

  const counts = {
    saju:   history.filter(e => e.type === 'saju').length,
    both:   history.filter(e => e.type === 'saju+tarot').length,
    tarot:  history.filter(e => e.type === 'tarot').length,
    compat: history.filter(e => e.type === 'compat' || e.type === 'compat+tarot').length,
  }

  return (
    <div className="max-w-[900px] mx-auto">
      <div className="flex items-center gap-3 flex-wrap mb-5">
        <h2 className="text-gold text-xl">📋 히스토리</h2>
        <div className="flex gap-2 flex-wrap flex-1">
          {[
            `총 ${history.length}건`,
            `사주 ${counts.saju}건`,
            `사주+타로 ${counts.both}건`,
            ...(counts.compat ? [`궁합 ${counts.compat}건`] : []),
            ...(counts.tarot ? [`타로 ${counts.tarot}건`] : []),
          ].map(label => (
            <span key={label} className="bg-app-card border border-p-600 text-p-100 px-2.5 py-1 rounded-xl text-xs">
              {label}
            </span>
          ))}
        </div>
        <div>
          {!confirmClear ? (
            <button
              onClick={() => setConfirmClear(true)}
              className="border border-[#604060] text-[#a080a0] px-3.5 py-1.5 rounded-lg text-xs hover:border-[#c06060] hover:text-[#e08080] transition-colors"
            >
              전체 삭제
            </button>
          ) : (
            <div className="flex items-center gap-2 text-xs text-[#e08080]">
              <span>정말 삭제?</span>
              <button onClick={() => { onClear(); setConfirmClear(false) }}
                className="bg-[#803030] text-white px-2.5 py-1 rounded-md">삭제</button>
              <button onClick={() => setConfirmClear(false)}
                className="bg-app-card border border-p-600 text-p-100 px-2.5 py-1 rounded-md">취소</button>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-2.5">
        {history.map(entry => (
          <HistoryEntry key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  )
}
