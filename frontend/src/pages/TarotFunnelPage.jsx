import { useState, useEffect, useRef } from 'react'
import '../funnel.css'
import { API, API_BASE } from '../api'
import TheaterFrame from '../components/TheaterFrame'
import ShuffleFan from '../components/ShuffleFan'
import OrderModal from '../components/OrderModal'
import PromoBanner from '../components/PromoBanner'
import useIsDesktop from '../hooks/useIsDesktop'
import imgHallWide from '../assets/funnel/hall_wide_1.jpg'

// 고삼타로 타로 몰입 퍼널 — 입장 → 스프레드 선택(10종) → 질문입력 → 카드뽑기(부채꼴) → 리빌(모바일=미니맵+순차/3장=세로컬럼, PC=배열펼침+리딩패널) → 페이월
// 출처: consulting/gosam_funnel/tarot_spread_conti.html · tarot_mobile_conti.html · funnel_tarot_pc_reveal.html
//   (디자인봇 확정, gate:gosam_tarot_spread_conti/gosam_tarot_mobile_conti 7/7)
// 🔴 이전(고정 3장 데모, Lovers/Wheel/Sun 항상 동일) → 실제 백엔드(/api/spreads, /api/tarot/draw) 연동으로 교체.
//   스프레드 10종 전부 하드코딩 없이 데이터로 렌더(col/row/gridCols/gridRows/cross는 백엔드가 줌).
//   AI 리딩(ai_available)이 꺼져있을 때는 정적 meaning/overall_summary로 자동 폴백(백엔드가 이미 그렇게 줌).

const SPREAD_GROUPS = [
  { label: '3장 · 질문유형', filter: s => s.cards === 3 },
  { label: '4·5장', filter: s => s.cards === 4 || s.cards === 5 },
  { label: '7장', filter: s => s.cards === 7 },
  { label: '10장', filter: s => s.cards === 10 },
]

const FAN_N = 7
const fanTransform = (i) => {
  const a = (i - (FAN_N - 1) / 2) * 11
  const x = (i - (FAN_N - 1) / 2) * 34
  return `rotate(${a}deg) translateX(${x}px) translateY(${Math.abs(a) * 0.9}px)`
}

const Rd = ({ children }) => <span className="rd">{children}</span>

// 백엔드 meaning 문장을 앞부분(공개)/뒷부분(블러) 대략 45% 지점 공백에서 분할 — 카드별 수기 카피 없이 데이터로 티저 생성
function splitTeaser(text, ratio = 0.45) {
  if (!text) return ['', '']
  const cut = Math.floor(text.length * ratio)
  const sp = text.indexOf(' ', cut)
  const idx = sp === -1 ? cut : sp
  return [text.slice(0, idx).trim(), text.slice(idx).trim()]
}

const cardImgUrl = (path) => path ? `${API_BASE}${path}` : ''

const Top = ({ onBack }) => (
  <>
    <div className="dancheong" />
    <div className="top"><button className="bk" onClick={onBack} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>←</button><span className="wm">고삼<b>타로</b></span></div>
  </>
)

function Minimap({ cards, gridCols, gridRows, activeIdx }) {
  const cw = Math.max(1, gridCols - 1)
  const ch = Math.max(1, gridRows - 1)
  return (
    <div className="minimap">
      {cards.map((c, i) => {
        const left = ((c.col + (c.cross ? 0.32 : 0)) / cw) * 100
        const top = ((c.row + (c.cross ? 0.32 : 0)) / ch) * 100
        return (
          <div key={i} className={`mnode${i < activeIdx ? ' done' : ''}${i === activeIdx ? ' on' : ''}`}
            style={{ left: `${left}%`, top: `${top}%` }}>{c.position_num}</div>
        )
      })}
    </div>
  )
}

function PcWideTarot({ onBack, bgPos, center, children }) {
  return (
    <div className="pcwide">
      <div className="bg" style={{ backgroundImage: `url('${imgHallWide}')`, backgroundPosition: bgPos || 'center 42%' }} />
      <div className="tint" /><div className="tint2" /><div className="dancheong" />
      <div className="topbar"><button className="bk" onClick={onBack}>‹</button><span className="wm serif">고삼<b>타로</b></span></div>
      <div className="wrap" style={center ? { justifyContent: 'center' } : undefined}>{children}</div>
    </div>
  )
}

function SpreadPicker({ spreads, onPick }) {
  return (
    <>
      {SPREAD_GROUPS.map(g => {
        const items = spreads.filter(g.filter)
        if (!items.length) return null
        return (
          <div key={g.label} className="spreadgrp">
            <h4>{g.label}</h4>
            <div className="spreadgrid">
              {items.map(s => (
                <button key={s.id} className="spreadcard" onClick={() => onPick(s.id)}>
                  <div className="stitle">{s.name}<span className="sn">{s.cards}장</span></div>
                  <div className="sdesc">{s.description}</div>
                </button>
              ))}
            </div>
          </div>
        )
      })}
    </>
  )
}

export default function TarotFunnelPage({ onBack: onExit }) {
  const [stage, setStage] = useState('select') // select|question|draw|reveal|paywall
  const [spreads, setSpreads] = useState([])
  const [spreadId, setSpreadId] = useState(null)
  const [question, setQuestion] = useState('')
  const [drawResult, setDrawResult] = useState(null)
  const [revealIdx, setRevealIdx] = useState(0)
  const [drawing, setDrawing] = useState(false)
  const [error, setError] = useState('')
  const [orderOpen, setOrderOpen] = useState(false)
  const isDesktop = useIsDesktop()

  useEffect(() => {
    fetch(`${API}/spreads`).then(r => r.json()).then(setSpreads).catch(() => setError('스프레드 목록을 불러오지 못했습니다'))
  }, [])

  const selectedSpread = spreads.find(s => s.id === spreadId)

  const doDraw = async () => {
    if (drawing) return
    setDrawing(true); setError('')
    try {
      const res = await fetch(`${API}/tarot/draw`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ spread_id: spreadId, question }),
      })
      if (!res.ok) throw new Error('draw fail')
      const data = await res.json()
      setDrawResult(data); setRevealIdx(0); setStage('reveal')
    } catch (e) {
      setError('카드를 뽑는 데 실패했습니다. 잠시 후 다시 시도해 주세요.')
    } finally { setDrawing(false) }
  }

  const nCards = drawResult?.cards?.length || 0
  const nextReveal = () => { if (revealIdx < nCards - 1) setRevealIdx(i => i + 1); else setStage('paywall') }
  const prevReveal = () => setRevealIdx(i => Math.max(0, i - 1))

  // 모바일 리빌화면 swipe 제스처 + 최초 1회 코치마크 — SajuFunnelPage와 동일 패턴(spo* 클래스 재사용)
  const [dragX, setDragX] = useState(0)
  const [dragging, setDragging] = useState(false)
  const touchStartX = useRef(0)
  const [coachSeen, setCoachSeen] = useState(() => {
    try { return localStorage.getItem('gosam_tarot_swipe_coach_seen') === '1' } catch { return true }
  })
  const chipbarRef = useRef(null)

  useEffect(() => {
    if (stage !== 'reveal' || nCards === 3 || revealIdx !== 0 || coachSeen) return
    const t = setTimeout(() => {
      setCoachSeen(true)
      try { localStorage.setItem('gosam_tarot_swipe_coach_seen', '1') } catch { /* noop */ }
    }, 1500)
    return () => clearTimeout(t)
  }, [stage, nCards, revealIdx, coachSeen])

  useEffect(() => {
    if (!chipbarRef.current) return
    const active = chipbarRef.current.querySelector('.spochip.active')
    if (active) active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }, [revealIdx])

  const onRevealTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; setDragging(true) }
  const onRevealTouchMove = (e) => {
    const dx = e.touches[0].clientX - touchStartX.current
    setDragX(Math.max(-120, Math.min(120, dx)))
  }
  const onRevealTouchEnd = () => {
    if (dragX <= -60) nextReveal()
    else if (dragX >= 60 && revealIdx > 0) prevReveal()
    setDragging(false)
    setDragX(0)
  }

  // ── 모바일(기본) 렌더 ──
  const mobileScreen = () => (
    <div className="funnel-root">
      <TheaterFrame screen={0} total={1} onPrev={() => {}} onNext={() => {}}>
        <div className="ph">
          {stage === 'select' && (
            <>
              <div className="stage" /><div className="texture" /><div className="ambient" />
              <Top onBack={onExit} />
              <div className="frameborder" /><div className="seal" style={{ right: 26, top: 92 }}>❖</div>
              <div className="content">
                <span className="ey">어떤 배열로 보시겠습니까</span>
                <div className="htitle">궁금한 <span className="r">결</span>에 맞는<br />배열을 고르십시오</div>
                {error && <div style={{ color: '#e08080', fontSize: 13, margin: '8px 0' }}>{error}</div>}
                <SpreadPicker spreads={spreads} onPick={(id) => { setSpreadId(id); setStage('question') }} />
              </div>
            </>
          )}

          {stage === 'question' && (
            <>
              <div className="stage" /><div className="texture" />
              <Top onBack={() => setStage('select')} />
              <div className="frameborder" /><div className="seal" style={{ right: 26, top: 92 }}>❖</div>
              <div className="content">
                <span className="ey">{selectedSpread?.name}</span>
                <div className="htitle">한 문장으로, <span className="g">묻고 싶은 것</span>을</div>
                <div className="hdesc">두루뭉술할수록 답도 흐려집니다. 정확히 물으십시오.</div>
                <label style={{ font: "700 13px system-ui", color: 'var(--gold2)', marginBottom: 7, display: 'block' }}>나의 질문</label>
                <textarea className="qbox" placeholder="예) 지금 그 사람은, 저를 다시 만날 마음이 있을까요?"
                  value={question} onChange={e => setQuestion(e.target.value)} />
                <div style={{ marginTop: 'auto' }}>
                  <button className="cta" onClick={() => setStage('draw')}>이 질문으로 카드 뽑기<small>물음을 정하시는 순간, 패가 섞입니다</small></button>
                </div>
              </div>
            </>
          )}

          {stage === 'draw' && (
            <>
              <div className="stage" /><div className="texture" /><div className="ambient" />
              <Top onBack={() => setStage('question')} />
              <div className="frameborder" />
              <div className="content">
                <span className="ey" style={{ textAlign: 'center', alignSelf: 'center' }}>패가 섞였습니다</span>
                <div className="htitle" style={{ textAlign: 'center' }}>마음을 비우시고,<br /><span className="g">한 장</span>을 고르십시오</div>
                <ShuffleFan n={FAN_N} fanTransform={fanTransform} onDraw={doDraw} drawing={drawing} />
                <div className="deal">{drawing ? '패를 살피는 중…' : '손이 멈추는 그 카드가, 당신의 패입니다'}</div>
                <div className="shuffle">{Array.from({ length: 5 }, (_, i) => <i key={i} />)}</div>
                {error && <div style={{ color: '#e08080', fontSize: 13, textAlign: 'center', marginTop: 10 }}>{error}</div>}
              </div>
            </>
          )}

          {stage === 'reveal' && drawResult && (
            nCards === 3 ? (
              <>
                <div className="stage" /><div className="texture" /><div className="ambient" />
                <Top onBack={() => setStage('draw')} />
                <div className="frameborder" />
                <div className="content">
                  <span className="ey">{drawResult.spread_name}</span>
                  <div className="htitle">세 자리의 <span className="g">카드</span></div>
                  <div className="stackcol" style={{ marginTop: 14 }}>
                    {drawResult.cards.map((c, i) => (
                      <div key={i} className="scard">
                        <img src={cardImgUrl(c.image)} alt="" />
                        <div className="sinfo">
                          <h4>{c.position_num}. {c.position_name}</h4>
                          <p>{c.position_desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <button className="cta" style={{ marginTop: 16 }} onClick={() => setStage('paywall')}>전체 풀이 보기<small>세 자리 종합 해석은 신당 안에서</small></button>
                </div>
              </>
            ) : (() => {
              const c = drawResult.cards[revealIdx]
              const [head, tail] = splitTeaser(c.meaning)
              return (
                <>
                  <div className="stage" /><div className="texture" /><div className="ambient" />
                  <Top onBack={() => setStage('draw')} />
                  <div className="frameborder" />
                  {/* 투명 tap존은 보조수단으로 유지, 주 수단은 아래 swipe+칩바+버튼 */}
                  <div className="navzone left" onClick={prevReveal} />
                  <div className="navzone right" onClick={nextReveal} />
                  <div className="content">
                    <Minimap cards={drawResult.cards} gridCols={drawResult.grid_cols} gridRows={drawResult.grid_rows} activeIdx={revealIdx} />
                    <div
                      className={`spocard${dragging ? ' dragging' : ''}`}
                      style={{ transform: `translateX(${dragX}px) rotate(${dragX / 60}deg)` }}
                      onTouchStart={onRevealTouchStart}
                      onTouchMove={onRevealTouchMove}
                      onTouchEnd={onRevealTouchEnd}
                    >
                      <div className="reveal">
                        <span className="cardpos" style={{ alignSelf: 'center' }}>🎴 {c.position_num}. {c.position_name}</span>
                        <div className="bigcard" style={{ backgroundImage: `url('${cardImgUrl(c.image)}')`, marginTop: 14 }} />
                        <div className="cardname">{c.card_name}{c.reversed ? ' (역방향)' : ''}</div>
                      </div>
                      <div className="reading">{head} <Rd>{tail}</Rd></div>
                      <div className="lockline">🔒 ▓ 카드의 전체 해석과 종합 결론은 신당 안에서 다 보여드립니다</div>
                      {dragX < -8 && revealIdx < nCards - 1 && <div className="nextpeek" />}
                    </div>
                    <div className="spochipbar" ref={chipbarRef}>
                      {drawResult.cards.map((card, i) => (
                        <button key={i} className={`spochip${i === revealIdx ? ' active' : i < revealIdx ? ' done' : ''}`} onClick={() => setRevealIdx(i)}>
                          {card.position_num}. {card.position_name}
                        </button>
                      ))}
                    </div>
                    <div className="spomnav">
                      <button className="spomprev" disabled={revealIdx === 0} onClick={prevReveal}>‹</button>
                      <button className="spomnext" onClick={nextReveal}>{revealIdx < nCards - 1 ? '다음 자리 ›' : '결과 보기 ›'}</button>
                    </div>
                  </div>
                  {revealIdx === 0 && !coachSeen && (
                    <div className="spocoach">
                      <div className="box">
                        <div className="finger">👆</div>
                        <div className="txt"><b>밀어서</b> 다음 카드</div>
                      </div>
                    </div>
                  )}
                </>
              )
            })()
          )}

          {stage === 'paywall' && drawResult && (
            <>
              <div className="stage" /><div className="texture" /><div className="ambient" />
              <Top onBack={() => setStage('reveal')} />
              <div className="frameborder" /><div className="seal" style={{ right: 26, top: 92 }}>❖</div>
              <div className="content">
                <span className="ey">여기까지가 무료 스포입니다</span>
                <div className="htitle">{drawResult.spread_name}, <span className="g">전체 뜻</span>과 결론은<br />신당 <span className="r">안에서</span></div>
                <div className="hdesc">어느 카드가, 무슨 말을 하는지. 흐릿한 건 제가 다 걷어 드립니다.</div>
                <div className="locked"><div className="blurcard">{drawResult.overall_summary}</div><div className="lockover">🔒</div></div>
                <PromoBanner />
                <div className="pricebox"><div className="p">₩ 7,900</div><div className="pn">{nCards}장 스프레드 전체 뜻 + 질문 종합 풀이</div><div className="mailrow">✉️ 완성 PDF, 이메일·카톡으로 배달</div></div>
                <button className="cta" onClick={() => setOrderOpen(true)}>전체 카드 풀이 받기<small>무통장 안전결제 · 24시간 내 배달</small></button>
                <button className="subline" style={{ marginTop: 12, background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setStage('select')}>처음으로 돌아가기</button>
              </div>
              <OrderModal open={orderOpen} onClose={() => setOrderOpen(false)} productKey="tarot_spread" amount={7900} productName={`${drawResult.spread_name} 전체 풀이`} />
            </>
          )}
        </div>
      </TheaterFrame>
    </div>
  )

  // ── PC 와이드(≥900px) 렌더 — select/question/draw/reveal/paywall ──
  const desktopScreen = () => {
    if (stage === 'select') {
      return (
        <div className="funnel-root">
          <PcWideTarot onBack={onExit}>
            <span className="ey">어떤 배열로 보시겠습니까</span>
            <div className="htitle">궁금한 결에 맞는 배열을 고르십시오</div>
            <div className="hdesc" style={{ marginBottom: 6 }}>장수가 많을수록 더 깊이 읽어 드립니다.</div>
            <div style={{ width: 900, maxWidth: '86vw' }}>
              {error && <div style={{ color: '#e08080', fontSize: 13, margin: '8px 0' }}>{error}</div>}
              <SpreadPicker spreads={spreads} onPick={(id) => { setSpreadId(id); setStage('question') }} />
            </div>
          </PcWideTarot>
        </div>
      )
    }
    if (stage === 'question') {
      return (
        <div className="funnel-root">
          <PcWideTarot onBack={() => setStage('select')}>
            <span className="ey">{selectedSpread?.name}</span>
            <div className="htitle" style={{ fontSize: 38, marginBottom: 26 }}>한 문장으로, <span className="g">묻고 싶은 것</span>을</div>
            <div className="panel">
              <div className="field"><label>나의 질문</label>
                <textarea className="inp" style={{ minHeight: 110 }} placeholder="예) 지금 그 사람은, 저를 다시 만날 마음이 있을까요?"
                  value={question} onChange={e => setQuestion(e.target.value)} />
              </div>
              <button className="cta serif" onClick={() => setStage('draw')}>이 질문으로 카드 뽑기<small>물음을 정하시는 순간, 패가 섞입니다</small></button>
            </div>
          </PcWideTarot>
        </div>
      )
    }
    if (stage === 'draw') {
      return (
        <div className="funnel-root">
          <PcWideTarot onBack={() => setStage('question')} center>
            <span className="ey" style={{ textAlign: 'center' }}>패가 섞였습니다</span>
            <div className="htitle" style={{ textAlign: 'center', marginBottom: 10 }}>마음을 비우시고, <span className="g">한 장</span>을 고르십시오</div>
            <ShuffleFan n={FAN_N} fanTransform={fanTransform} onDraw={doDraw} drawing={drawing} />
            <div className="deal">{drawing ? '패를 살피는 중…' : '손이 멈추는 그 카드가, 당신의 패입니다'}</div>
            {error && <div style={{ color: '#e08080', fontSize: 13, textAlign: 'center', marginTop: 10 }}>{error}</div>}
          </PcWideTarot>
        </div>
      )
    }
    if (stage === 'reveal' && drawResult) {
      const gc = drawResult.grid_cols, gr = drawResult.grid_rows
      return (
        <div className="funnel-root">
          <PcWideTarot onBack={() => setStage('draw')} center bgPos="center 40%">
            <div className="revealwide">
              <div className="revealgrid" style={{ gridTemplateColumns: `repeat(${gc},104px)`, gridTemplateRows: `repeat(${gr},168px)` }}>
                {drawResult.cards.map((c, i) => (
                  <div key={i} className={`gcard${c.cross ? ' cross' : ''}${i === revealIdx ? ' on' : i > revealIdx ? ' dim' : ''}`}
                    style={{ gridColumn: c.col + 1, gridRow: c.row + 1 }} onClick={() => setRevealIdx(i)}>
                    <img src={i <= revealIdx ? cardImgUrl(c.image) : undefined} alt="" />
                    <div className="glabel">{c.position_num}. {c.position_name}</div>
                  </div>
                ))}
              </div>
              <div className="panel2">
                {(() => {
                  const c = drawResult.cards[revealIdx]
                  const [head, tail] = splitTeaser(c.meaning)
                  return (
                    <>
                      <span className="pcardpos">🎴 {c.position_num}. {c.position_name}</span>
                      <div className="pname serif">{c.card_name}{c.reversed ? ' (역방향)' : ''}</div>
                      <div className="preading">{head} <Rd>{tail}</Rd></div>
                      <div className="plock">🔒 카드의 전체 해석과 종합 결론은 신당 안에서 다 보여드립니다</div>
                      <div className="pnav">
                        <button disabled={revealIdx === 0} onClick={prevReveal}>← 이전 자리</button>
                        <button className="next" onClick={nextReveal}>{revealIdx < nCards - 1 ? '다음 자리 →' : '결과 보기 →'}</button>
                      </div>
                    </>
                  )
                })()}
              </div>
            </div>
          </PcWideTarot>
        </div>
      )
    }
    if (stage === 'paywall' && drawResult) {
      return (
        <div className="funnel-root">
          <PcWideTarot onBack={() => setStage('reveal')}>
            <span className="ey">여기까지가 무료 스포입니다</span>
            <div className="htitle" style={{ fontSize: 36, marginBottom: 26 }}>{drawResult.spread_name}, <span className="g">전체 뜻</span>과 결론은 신당 <span className="r">안에서</span></div>
            <div className="hdesc" style={{ marginBottom: 18 }}>어느 카드가, 무슨 말을 하는지. 흐릿한 건 제가 다 걷어 드립니다.</div>
            <div className="locked"><div className="blur">{drawResult.overall_summary}</div><div className="ov">🔒</div></div>
            <PromoBanner />
            <div className="pricebox"><div className="p">₩ 7,900</div><div className="pn">{nCards}장 스프레드 전체 뜻 + 질문 종합 풀이 · 완성 PDF 배달</div></div>
            <button className="cta serif" style={{ width: 520 }} onClick={() => setOrderOpen(true)}>전체 카드 풀이 받기<small>무통장 안전결제 · 24시간 내 배달</small></button>
            <button className="pcback" onClick={() => setStage('select')}>처음으로 돌아가기</button>
            <OrderModal open={orderOpen} onClose={() => setOrderOpen(false)} productKey="tarot_spread" amount={7900} productName={`${drawResult.spread_name} 전체 풀이`} />
          </PcWideTarot>
        </div>
      )
    }
    return mobileScreen()
  }

  return isDesktop ? desktopScreen() : mobileScreen()
}
