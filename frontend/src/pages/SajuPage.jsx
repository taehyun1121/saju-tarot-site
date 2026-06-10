import { useState } from 'react'

const EMPTY_PERSON = { name:'', year:'', month:'', day:'', hour:'', minute:'', gender:'남' }

function PersonForm({ person, index, onChange, onRemove, canRemove, label }) {
  const update = (field, val) => onChange(index, { ...person, [field]: val })
  return (
    <div className="bg-app-deep border border-p-700 rounded-xl p-4 mb-3 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-p-50 font-bold text-sm">
          {label || (index === 0 ? '👤 대상자 1 (메인)' : `👤 대상자 ${index + 1}`)}
        </span>
        {canRemove && (
          <button onClick={() => onRemove(index)}
            className="border border-[#6a2040] text-[#c06080] px-3 py-1 rounded-md text-xs hover:bg-[#3a1020] transition-colors">
            ✕ 삭제
          </button>
        )}
      </div>
      <div className="flex flex-col gap-1.5">
        <label className="text-p-200 text-xs">이름 / 별칭</label>
        <input type="text" placeholder="예: 홍길동, 상대방, 나 …"
          value={person.name} onChange={e => update('name', e.target.value)}
          className="bg-app-input border border-p-600 rounded-lg px-3 py-2 text-p-10 text-sm outline-none focus:border-p-300 placeholder:text-[#4a3870] w-full" />
      </div>

      <div className="flex gap-2 flex-wrap">
        {[
          { label:'년도 *', field:'year', placeholder:'예: 1990', min:1900, max:2025 },
          { label:'월 *',   field:'month', placeholder:'1~12',    min:1,    max:12 },
          { label:'일 *',   field:'day',   placeholder:'1~31',    min:1,    max:31 },
        ].map(({ label, field, placeholder, min, max }) => (
          <div key={field} className="flex flex-col gap-1.5 flex-1 min-w-[78px]">
            <label className="text-p-200 text-xs">{label}</label>
            <input type="number" placeholder={placeholder} min={min} max={max}
              value={person[field]} onChange={e => update(field, e.target.value)}
              className="bg-app-input border border-p-600 rounded-lg px-3 py-2 text-p-10 text-sm outline-none focus:border-p-300 placeholder:text-[#4a3870] w-full" />
          </div>
        ))}
      </div>
      <div className="flex gap-2 flex-wrap">
        {[
          { label:'시간 (0~23)', field:'hour',   placeholder:'모르면 비움', min:0, max:23 },
          { label:'분 (0~59)',   field:'minute', placeholder:'모르면 비움', min:0, max:59 },
        ].map(({ label, field, placeholder, min, max }) => (
          <div key={field} className="flex flex-col gap-1.5 flex-1 min-w-[78px]">
            <label className="text-p-200 text-xs">{label}</label>
            <input type="number" placeholder={placeholder} min={min} max={max}
              value={person[field]} onChange={e => update(field, e.target.value)}
              className="bg-app-input border border-p-600 rounded-lg px-3 py-2 text-p-10 text-sm outline-none focus:border-p-300 placeholder:text-[#4a3870] w-full" />
          </div>
        ))}
        <div className="flex flex-col gap-1.5 flex-1 min-w-[78px]">
          <label className="text-p-200 text-xs">성별</label>
          <div className="flex gap-2">
            {['남','여'].map(g => (
              <button key={g} type="button" onClick={() => update('gender', g)}
                className={`flex-1 py-2 border rounded-lg text-sm whitespace-nowrap min-w-[44px] transition-all
                  ${person.gender === g ? 'bg-p-400 border-p-300 text-white' : 'bg-transparent border-p-600 text-p-200 hover:border-p-400'}`}>
                {g}성
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Accordion({ items, accentColor = 'bg-p-400' }) {
  return (
    <div className="flex flex-col gap-3">
      {items.map((item, i) => (
        <div key={i} className="border border-p-700 rounded-lg overflow-hidden">
          <div className="flex items-center gap-2.5 bg-app-input px-3.5 py-2.5">
            <span className={`w-5 h-5 ${accentColor} rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0`}>{i+1}</span>
            <span className="flex-1 text-p-10 text-sm font-semibold max-sm:text-xs">{item.title}</span>
          </div>
          <div className="px-3.5 py-3 bg-app-dark text-p-100 text-sm leading-relaxed border-t border-p-700 max-sm:text-xs">
            {item.content}
          </div>
        </div>
      ))}
    </div>
  )
}

function PillarDisplay({ pillars }) {
  return (
    <div className="flex gap-2 mb-3 flex-wrap">
      {['year','month','day','hour'].map(k => (
        pillars[k] ? (
          <div key={k} className={`flex-1 min-w-[58px] bg-app-input border rounded-xl py-3 px-1 text-center ${k==='day'?'border-gold':'border-p-600'}`}>
            <div className="text-p-200 text-xs mb-1">{k==='year'?'년주':k==='month'?'월주':k==='day'?'일주':'시주'}</div>
            <div className="text-p-10 text-xl tracking-widest mb-1 max-sm:text-base">{pillars[k].hanja}</div>
            <div className="text-p-150 text-xs">{pillars[k].korean}</div>
          </div>
        ) : (
          <div key={k} className="flex-1 min-w-[58px] bg-app-input border border-p-600 rounded-xl py-3 px-1 text-center opacity-40">
            <div className="text-p-200 text-xs mb-1">시주</div>
            <div className="text-p-600 text-xl mb-1">??</div>
            <div className="text-p-150 text-xs">모름</div>
          </div>
        )
      ))}
    </div>
  )
}

const STATUS_STYLE = {
  '과거': 'border-p-600 text-p-300 bg-app-input',
  '현재': 'border-gold text-gold bg-[#1a1500]',
  '미래': 'border-p-400 text-p-100 bg-[#0d0a1a]',
}

function DecadeTimeline({ decades }) {
  const [open, setOpen] = useState(null)
  if (!decades?.length) return null
  return (
    <div className="flex flex-col gap-2">
      {decades.map((d, i) => (
        <div key={i} className={`border rounded-xl overflow-hidden ${STATUS_STYLE[d.status] || 'border-p-600 text-p-200 bg-app-input'}`}>
          <button onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center gap-3 px-4 py-3 text-left">
            <span className="text-base font-bold w-10 shrink-0">{d.label}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border shrink-0
              ${d.status === '현재' ? 'border-gold text-gold bg-[#2a2000]'
              : d.status === '과거' ? 'border-p-600 text-p-350 bg-app-deep'
              : 'border-p-400 text-p-200 bg-app-deep'}`}>
              {d.status}
            </span>
            <span className="flex-1 text-xs text-p-300 truncate">{d.content?.slice(0, 40)}…</span>
            <span className="text-p-400 text-xs shrink-0">{open === i ? '▲' : '▼'}</span>
          </button>
          {open === i && (
            <div className="px-4 pb-4 text-sm leading-relaxed border-t border-p-700 pt-3 text-p-100">
              {d.content}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

/* ── 별도 사주 결과 ── */
function ResultCard({ result, person, index, historyId, onGoToTarot }) {
  const [tab, setTab] = useState('ai')

  return (
    <div className="bg-app-card border border-p-600 rounded-xl p-6 flex flex-col gap-4 max-sm:p-4">
      <h3 className="text-gold text-lg">
        🔮 {person?.name ? person.name : `대상자 ${index + 1}`} 사주풀이
      </h3>

      {/* 만세력 */}
      <div className="bg-app-dark border border-p-700 rounded-xl p-4">
        <PillarDisplay pillars={result.pillars} />
        <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-p-700 mt-1">
          <span className="text-p-200 text-xs min-w-[40px]">대운</span>
          {result.daeun.slice(0,6).map((d,i) => (
            <span key={i} className={`text-xs px-2 py-0.5 rounded-md border ${i===2?'border-gold text-gold':'border-p-700 text-p-100 bg-app-input'}`}>
              {d.hanja}<small className="text-p-350 ml-1 text-[0.65rem] max-sm:hidden">({d.start}~{d.end})</small>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2 pt-2 border-t border-p-700 mt-2">
          <span className="text-p-200 text-xs min-w-[60px]">2026 세운</span>
          <span className="text-gold font-bold">{result.seun}</span>
        </div>
      </div>

      {/* 탭 */}
      <div className="flex gap-2 flex-wrap">
        {result.ai_available && (
          <button onClick={() => setTab('ai')}
            className={`flex-1 min-w-[80px] py-2 rounded-lg text-sm font-medium border transition-all
              ${tab === 'ai' ? 'bg-p-400 border-p-300 text-white' : 'bg-transparent border-p-600 text-p-200 hover:border-p-400'}`}>
            ✨ Gemini 해석
          </button>
        )}
        {result.decade_readings?.length > 0 && (
          <button onClick={() => setTab('decade')}
            className={`flex-1 min-w-[80px] py-2 rounded-lg text-sm font-medium border transition-all
              ${tab === 'decade' ? 'bg-[#2a1a00] border-gold text-gold' : 'bg-transparent border-p-600 text-p-200 hover:border-p-400'}`}>
            📅 연대별 인생
          </button>
        )}
        <button onClick={() => setTab('raw')}
          className={`flex-1 min-w-[80px] py-2 rounded-lg text-sm font-medium border transition-all
            ${tab === 'raw' ? 'bg-p-400 border-p-300 text-white' : 'bg-transparent border-p-600 text-p-200 hover:border-p-400'}`}>
          📋 사주 데이터
        </button>
      </div>

      {/* Gemini 해석 탭 */}
      {tab === 'ai' && result.ai_available && (
        <div className="flex flex-col gap-3">
          <div className="bg-app-dark border border-p-700 rounded-xl p-4">
            <h4 className="text-p-50 text-sm mb-3">✨ Gemini 사주 해석</h4>
            <Accordion items={result.ai_readings} />
          </div>
          {result.ai_overall && (
            <div className="bg-app-deep border border-gold rounded-xl p-4">
              <h4 className="text-gold text-sm mb-2">🌟 종합 운세</h4>
              <p className="text-p-100 text-sm leading-relaxed">{result.ai_overall}</p>
            </div>
          )}
        </div>
      )}

      {/* 연대별 인생 탭 */}
      {tab === 'decade' && result.decade_readings?.length > 0 && (
        <div className="bg-app-dark border border-p-700 rounded-xl p-4">
          <h4 className="text-gold text-sm mb-3">📅 연대별 인생 흐름</h4>
          <DecadeTimeline decades={result.decade_readings} />
        </div>
      )}

      {/* 사주 데이터 탭 */}
      {tab === 'raw' && (
        <div className="bg-app-dark border border-p-700 rounded-xl p-4">
          <h4 className="text-p-50 text-sm mb-3">14항목 풀이</h4>
          <Accordion items={result.reading} />
        </div>
      )}

      <button onClick={() => onGoToTarot({ ...result, historyId, personName: person?.name || null })}
        className="self-stretch sm:self-start bg-gradient-to-br from-rose-accent to-pink-accent text-white px-5 py-3 rounded-lg font-bold text-sm tracking-wide hover:opacity-85 transition-opacity text-center">
        🃏 {person?.name ? `${person.name} 사주로 타로 보기` : '이 사주로 타로 보기'} →
      </button>
    </div>
  )
}

/* ── 궁합 결과 ── */
function CompatibilityCard({ result, persons, historyId, onGoToTarot }) {
  const { person1, person2, reading } = result
  const typeLabel = { saju: '사주', compat: '궁합' }

  return (
    <div className="bg-app-card border border-[#5a3080] rounded-xl p-6 flex flex-col gap-4 max-sm:p-4">
      <div className="flex items-center gap-3">
        <h3 className="text-gold text-lg">💫 궁합 풀이</h3>
        <span className="bg-[#3a2060] text-[#c080ff] border border-[#5a3080] px-2.5 py-0.5 rounded-full text-xs">
          {person1.pillars.day.hanja} × {person2.pillars.day.hanja}
        </span>
      </div>

      {/* 두 사람 사주 나란히 */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { data: person1, person: persons[0] },
          { data: person2, person: persons[1] },
        ].map(({ data, person }, idx) => (
          <div key={idx} className="bg-app-dark border border-p-700 rounded-xl p-3">
            <div className="text-p-200 text-xs mb-2 font-bold">
              {person?.name || `대상${idx + 1}`}
              <span className="text-p-350 font-normal ml-1">({person?.year}/{person?.month}/{person?.day} {person?.gender})</span>
            </div>
            <div className="flex gap-1 flex-wrap">
              {['year','month','day','hour'].map(k => (
                data.pillars[k] ? (
                  <div key={k} className={`flex-1 min-w-[44px] bg-app-input border rounded-lg py-2 px-0.5 text-center ${k==='day'?'border-gold':'border-p-600'}`}>
                    <div className="text-p-200 text-[0.6rem] mb-0.5">{k==='year'?'년':k==='month'?'월':k==='day'?'일':'시'}</div>
                    <div className="text-p-10 text-sm font-bold">{data.pillars[k].hanja}</div>
                  </div>
                ) : null
              ))}
            </div>
            <div className="mt-2 text-p-200 text-xs">일간: <span className="text-gold font-bold">{data.ilgan}</span></div>
          </div>
        ))}
      </div>

      {/* 궁합 분석 */}
      <div className="bg-app-dark border border-p-700 rounded-xl p-4">
        <h4 className="text-[#c080ff] text-sm mb-3">궁합 분석 ({reading.length}항목)</h4>
        <Accordion items={reading} accentColor="bg-[#5a3080]" />
      </div>

      <button
        onClick={() => onGoToTarot({
          type: 'compat',
          person1, person2,
          person1Name: persons[0]?.name || null,
          person2Name: persons[1]?.name || null,
          historyId,
          pillars: person1.pillars,
          ilgan: person1.ilgan,
        })}
        className="self-stretch sm:self-start bg-gradient-to-br from-[#5a2060] to-[#8030a0] text-white px-5 py-3 rounded-lg font-bold text-sm tracking-wide hover:opacity-85 transition-opacity text-center">
        🃏 두 사람의 궁합 타로 보기 →
      </button>
    </div>
  )
}

/* ── 메인 페이지 ── */
export default function SajuPage({ onGoToTarot, onSaveHistory }) {
  const [persons, setPersons] = useState([{ ...EMPTY_PERSON }])
  const [mode, setMode] = useState('separate')   // 'separate' | 'compat'
  const [results, setResults] = useState([])
  const [compatResult, setCompatResult] = useState(null)
  const [historyIds, setHistoryIds] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const updatePerson = (index, updated) => setPersons(prev => prev.map((p, i) => i === index ? updated : p))
  const addPerson = () => {
    if (mode === 'compat' && persons.length >= 2) return
    setPersons(prev => [...prev, { ...EMPTY_PERSON }])
  }
  const removePerson = (index) => {
    setPersons(prev => prev.filter((_, i) => i !== index))
    setResults(prev => prev.filter((_, i) => i !== index))
  }

  const toReq = p => ({
    year: Number(p.year), month: Number(p.month), day: Number(p.day),
    hour: p.hour !== '' ? Number(p.hour) : null,
    minute: p.minute !== '' ? Number(p.minute) : null,
    gender: p.gender,
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    for (let i = 0; i < persons.length; i++) {
      if (!persons[i].year || !persons[i].month || !persons[i].day) {
        setError(`대상자 ${i+1}: 년/월/일은 필수입니다`)
        return
      }
    }
    setLoading(true)
    setResults([])
    setCompatResult(null)

    try {
      if (mode === 'compat' && persons.length === 2) {
        // 궁합 모드
        const res = await fetch('/api/compatibility', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ person1: toReq(persons[0]), person2: toReq(persons[1]) })
        }).then(r => r.json())
        setCompatResult(res)
        const id = `${Date.now()}_compat`
        setHistoryIds([id])
        if (onSaveHistory) {
          onSaveHistory([{
            id, timestamp: new Date().toISOString(), type: 'compat',
            person: persons[0], person2: persons[1], compat: res, tarot: null,
          }])
        }
      } else {
        // 별도 풀이 모드
        const responses = await Promise.all(persons.map(p =>
          fetch('/api/saju', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(toReq(p)) }).then(r => r.json())
        ))
        setResults(responses)
        const now = Date.now()
        const ids = responses.map((_, i) => `${now}_${i}`)
        setHistoryIds(ids)
        if (onSaveHistory) {
          const entries = responses
            .map((result, i) => ({ id: ids[i], timestamp: new Date(now).toISOString(), type: 'saju', person: persons[i], saju: result, tarot: null }))
            .filter(e => e.saju?.pillars)
          if (entries.length > 0) onSaveHistory(entries)
        }
      }
    } catch {
      setError('서버 연결 오류. 백엔드가 실행 중인지 확인하세요.')
    }
    setLoading(false)
  }

  const submitLabel = mode === 'compat' ? '💫 궁합 보기' : '🔮 사주풀이 보기'

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-app-card border border-p-600 rounded-xl p-6 max-sm:p-4">
        <h2 className="text-gold text-xl mb-5 max-sm:text-lg max-sm:mb-3">🔮 사주풀이</h2>

        <form onSubmit={handleSubmit}>
          {persons.map((person, i) => (
            <PersonForm key={i} person={person} index={i}
              onChange={updatePerson} onRemove={removePerson}
              canRemove={persons.length > 1}
              label={mode === 'compat' ? (i === 0 ? '👤 나 (대상1)' : '👥 상대 (대상2)') : null}
            />
          ))}

          {/* 모드 선택 — 대상자 2명일 때 표시 */}
          {persons.length >= 2 && (
            <div className="flex items-center gap-2 mb-4 p-3 bg-app-deep border border-p-700 rounded-xl">
              <span className="text-p-200 text-xs mr-1">풀이 방식</span>
              {[
                { val: 'separate', label: '별도 사주풀이' },
                { val: 'compat',   label: '💫 궁합 보기' },
              ].map(opt => (
                <button key={opt.val} type="button"
                  onClick={() => setMode(opt.val)}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all border
                    ${mode === opt.val
                      ? opt.val === 'compat'
                        ? 'bg-[#3a2060] border-[#7040b0] text-[#c080ff]'
                        : 'bg-p-400 border-p-300 text-white'
                      : 'bg-transparent border-p-600 text-p-200 hover:border-p-400'}`}>
                  {opt.label}
                </button>
              ))}
            </div>
          )}

          <div className="flex gap-3 mt-1 max-[360px]:flex-col">
            {!(mode === 'compat' && persons.length >= 2) && (
              <button type="button" onClick={addPerson}
                className="flex-1 bg-transparent border border-dashed border-p-400 text-p-200 py-3 rounded-lg text-sm hover:border-p-300 hover:text-p-100 hover:bg-app-hover transition-all">
                + 대상자 추가
              </button>
            )}
            <button type="submit" disabled={loading}
              className={`py-3 rounded-lg font-bold tracking-wide text-base hover:opacity-85 disabled:opacity-50 transition-opacity max-[360px]:w-full
                ${mode === 'compat' && persons.length >= 2
                  ? 'w-full bg-gradient-to-br from-[#5a2060] to-[#8030a0] text-white'
                  : 'flex-[2] bg-gradient-to-br from-p-400 to-p-300 text-white'}`}>
              {loading ? '계산 중...' : submitLabel}
            </button>
          </div>

          {error && <p className="text-[#ff8080] text-sm mt-2">{error}</p>}
        </form>
      </div>

      {/* 결과 */}
      {compatResult && (
        <CompatibilityCard result={compatResult} persons={persons}
          historyId={historyIds[0]} onGoToTarot={onGoToTarot} />
      )}
      {results.map((result, i) => (
        <ResultCard key={i} result={result} person={persons[i]} index={i}
          historyId={historyIds[i]} onGoToTarot={onGoToTarot} />
      ))}
    </div>
  )
}
