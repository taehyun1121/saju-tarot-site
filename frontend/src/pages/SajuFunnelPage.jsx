import { useState, useEffect, useRef } from 'react'
import { API } from '../api'
import '../funnel.css'
import TheaterFrame from '../components/TheaterFrame'
import PcIntroScreen from '../components/PcIntroScreen'
import MobileIntroScreen from '../components/MobileIntroScreen'
import OrderModal from '../components/OrderModal'
import useIsDesktop from '../hooks/useIsDesktop'
import imgEmTarot from '../assets/funnel/em_tarot_blue.jpg'
import imgEmSaju from '../assets/funnel/em_saju_blue.jpg'
import imgEmChong from '../assets/funnel/em_chong_blue.jpg'
import imgHallWide from '../assets/funnel/hall_wide_1.jpg'
import imgTileTarot from '../assets/funnel/tile_tarot.jpg'
import imgTileSaju from '../assets/funnel/tile_saju.jpg'
import imgTileChong from '../assets/funnel/tile_chong.jpg'

// 고삼타로 몰입 퍼널 — 랜딩→선택→입력→스포(대박·조심·연애·결혼)→페이월
// 출처: consulting/gosam_funnel/funnel_blue.html (디자인봇 확정, gate:gosam_funnel_reskin 7/7) — 블루골드 신당 리스킨(2026-07-19)
// 🔴 정직한 범위: 입력→백엔드 /api/saju 실연동됨. 4대운 피크 전용 엔진(saju_fortune_curve.py)은
//   '대박운'·'조심할 시기' 카드의 헤드라인연도+그래프만 실데이터 연동 완료(spoSpecs 함수 주석 참고).
//   '연애운'·'결혼운'은 원 디자인의 페이월 블러 의도와 엔진 데이터 정밀도가 안 맞아 데모 카피 유지(미완, 디자인봇 판단 필요).
//   결제·PDF 배달은 버튼만 있고 미연동(후속).

const TILES = [
  { id: 'tarot', title: '타로의 문 — 지금 이 순간', desc: '당장 궁금한 그 일의 흐름', img: imgEmTarot },
  { id: 'saju', title: '사주의 문 — 타고난 판', desc: '재물·연애·시기의 큰 그림', img: imgEmSaju },
  { id: 'chong', title: '올해 총운의 문', desc: '올 한 해, 열리고 닫히는 문', img: imgEmChong },
]

// PC 와이드 선택화면용 리치 썸네일(모바일 TILES와 이미지·문구 분할만 다름, 내용은 동일)
const PC_TILES = [
  { id: 'tarot', h3: '타로의 문', desc: '지금 이 순간, 당장 궁금한 그 일의 흐름', img: imgTileTarot },
  { id: 'saju', h3: '사주의 문', desc: '타고난 판 — 재물·연애·시기의 큰 그림', img: imgTileSaju },
  { id: 'chong', h3: '올해 총운의 문', desc: '올 한 해, 열리고 닫히는 문', img: imgTileChong },
]

// PC 와이드 화면 공용 셸(배경+틴트+단청+상단바+wrap) — 출처: funnel_pc_screens.html
// 🔴 코코 추가(2026-07-20, 실사용자 피드백): onPrev/onNext 주면 방향키(←/→)+휠스크롤로도 넘어가게.
// 도트만으로는 "눌러야 넘어간다"는 게 안 보인다는 지적 → PC 스포 화면에 명시적 이전/다음 버튼도 별도로 추가.
function PcWide({ onBack, bgPos, center, children, onPrev, onNext, prevDisabled, nextDisabled }) {
  useEffect(() => {
    if (!onPrev && !onNext) return
    const onKey = (e) => {
      if (e.key === 'ArrowLeft' && onPrev) onPrev()
      else if (e.key === 'ArrowRight' && onNext) onNext()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onPrev, onNext])
  const wheelLock = useRef(false)
  const onWheel = (e) => {
    if (!onPrev && !onNext) return
    if (wheelLock.current || Math.abs(e.deltaY) < 20) return
    wheelLock.current = true
    if (e.deltaY > 0) { if (onNext) onNext() } else { if (onPrev) onPrev() }
    setTimeout(() => { wheelLock.current = false }, 500)
  }
  return (
    <div className="pcwide" onWheel={onWheel}>
      <div className="bg" style={{ backgroundImage: `url('${imgHallWide}')`, backgroundPosition: bgPos || 'center 42%' }} />
      <div className="tint" /><div className="tint2" /><div className="dancheong" />
      <div className="topbar"><button className="bk" onClick={onBack}>‹</button><span className="wm serif">고삼<b>타로</b></span></div>
      {onPrev && <button className={`edge L${prevDisabled ? ' dim' : ''}`} onClick={onPrev} aria-label="이전 운세">‹</button>}
      {onNext && <button className={`edge R${nextDisabled ? ' dim' : ''}`} onClick={onNext} aria-label="다음 운세">›</button>}
      <div className="wrap" style={center ? { justifyContent: 'center' } : undefined}>{children}</div>
    </div>
  )
}

function Graph({ pts, peakX, color }) {
  const w = 336, h = 118
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' ')
  const gid = `g${peakX}${color.replace('#', '')}`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: 118 }}>
      <defs><linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor={color} stopOpacity=".35" /><stop offset="1" stopColor={color} stopOpacity="0" />
      </linearGradient></defs>
      <path d={`${path} L${w},${h} L0,${h} Z`} fill={`url(#${gid})`} />
      <path d={path} fill="none" stroke={color} strokeWidth="2.5" />
      <circle cx={peakX} cy="14" r="5" fill="#e3c069" />
      <line x1={peakX} y1="14" x2={peakX} y2={h} stroke="#e3c069" strokeDasharray="3 4" strokeWidth="1" />
    </svg>
  )
}

const Rd = ({ children }) => <span className="rd">{children}</span>

// 그래프 y좌표 정규화(score 0~100 → svg y 10~108, 높을수록 위)
const scoreToY = (score) => Math.round(10 + (100 - Math.max(0, Math.min(100, score))) / 100 * 98)

// peak_windows[cat](±2세, 1년간격 5점, saju_fortune_curve.py 실계산값)를 그래프 pts/yrs/peakX로 변환.
// 미확정이거나 데이터가 없으면 null 반환 → 호출부에서 데모값 폴백.
function realGraphFrom(window) {
  if (!window || window.length < 2) return null
  const n = window.length
  const step = 336 / (n - 1)
  const pts = window.map((c, i) => [Math.round(i * step), scoreToY(c.score)])
  const yrs = window.map((c) => `'${String(c.year).slice(-2)}`)
  const peakX = pts[Math.floor(n / 2)][0]
  return { pts, yrs, peakX }
}

// 4대운 화면 스펙 — 그래프/헤드라인 연도는 실데이터(fortune.peak_windows) 연동됨.
// 🔴 정직한 범위: '대박운'·'조심할 시기'는 디자인상 원래도 정확 연도를 무료로 보여주는
//   카드라 실제 계산 연도로 교체함. '연애운'·'결혼운'은 원 디자인이 계절/정확연도를
//   의도적으로 블러(페이월 유도) 처리해뒀는데, 백엔드 엔진은 월·계절 단위 데이터를 안 주고
//   (지어내기 금지 원칙) 정확 연도만 주기 때문에 그대로 노출하면 블러 의미가 없어짐 —
//   그래서 이 두 카드는 시안 데모 카피/그래프를 그대로 유지(디자인봇 판단 필요, 미완).
//   reading 문단(구체 서사)은 엔진이 안 주는 정보라 전 카드 데모 카피 유지.
function spoSpecs(sajuResult) {
  const windows = sajuResult?.fortune?.peak_windows
  const peaks = sajuResult?.fortune?.peaks
  const bigLuck = realGraphFrom(windows?.['대박운'])
  const bigLuckYear = peaks?.['대박운']?.year
  const risk = realGraphFrom(windows?.['조심시기'])
  const riskYear = peaks?.['조심시기']?.year

  return [
    {
      badge: '대박운', ico: '💰',
      hl: bigLuckYear ? `${bigLuckYear}년,` : '2026년,', rest: '재물의 문이 크게 열립니다',
      yrs: bigLuck?.yrs || ["'24", "'25", "'26", "'27", "'28"],
      pts: bigLuck?.pts || [[0, 92], [84, 74], [168, 20], [252, 52], [336, 40]],
      peakX: bigLuck?.peakX ?? 168, color: '#e0b84a',
      reading: <>재물의 문이 열리는 시작은 <b>봄</b>입니다. 다만 손에 쥔 그 일이 아니라, <Rd>▓▓▓</Rd>를 통해 들어옵니다. 규모는 <Rd>▓,▓▓▓</Rd>만원 선. 단, <Rd>▓월</Rd>에 들어올 제안 하나만은 반드시 걸러 보셔야 합니다.</>,
    },
    {
      badge: '조심할 시기', ico: '⚠️',
      hl: riskYear ? `${riskYear}년,` : '2025년 늦가을,', rest: '한 번 크게 흔들리십니다',
      yrs: risk?.yrs || ["'24", "'25", "'26", "'27", "'28"],
      pts: risk?.pts || [[0, 40], [84, 58], [168, 100], [252, 66], [336, 44]],
      peakX: risk?.peakX ?? 168, color: '#c0392b',
      reading: <>흔들림의 불씨는 돈이 아니라 <b>사람</b>입니다. 그중에서도 <Rd>▓▓ 관계</Rd>. 고비는 <Rd>▓월 ▓주</Rd>에 몰려 있으니, 그때 <Rd>▓▓▓</Rd>만 삼가시면 큰 손해는 피하십니다.</>,
    },
    {
      badge: '연애운', ico: '💗', hl: '내년 여름,', rest: '묶였던 인연이 풀립니다',
      yrs: ["'24", "'25", "'26", "'27", "'28"], pts: [[0, 80], [84, 70], [168, 44], [252, 18], [336, 34]], peakX: 252, color: '#d46a8a',
      reading: <>그 사람은 낯선 이가 아니라, 이미 <Rd>▓▓에서 스친</Rd> 얼굴입니다. 결은 <Rd>▓▓</Rd> 계열. 먼저 손 내미는 쪽은 <Rd>▓쪽</Rd>이 유리하고, 신호는 <Rd>▓월</Rd>부터 잡힙니다.</>,
    },
    {
      badge: '결혼운', ico: '💍', hl: '20▓▓년,', rest: '혼사의 문이 열립니다',
      yrs: ["'26", "'27", "'28", "'29", "'30"], pts: [[0, 88], [84, 60], [168, 50], [252, 24], [336, 16]], peakX: 336, color: '#e0b84a',
      reading: <>상대의 결은 <Rd>▓▓하고 ▓▓한</Rd> 사람입니다. 적기는 <Rd>▓월경</Rd>. 다만 그 전에 <Rd>▓▓</Rd> 한 가지를 매듭짓지 않으시면, 문이 열려도 들어서기 어렵습니다.</>,
    },
  ]
}

const Top = ({ onBack }) => (
  <>
    <div className="dancheong" />
    <div className="top"><button className="bk" onClick={onBack}>←</button><span className="wm">고삼<b>타로</b></span></div>
  </>
)

export default function SajuFunnelPage({ onSelectTarot }) {
  const [screen, setScreen] = useState(0)   // 0=랜딩 1=선택 2=입력 3~6=스포 7=페이월
  const [form, setForm] = useState({ year: '', month: '', day: '', hour: '', gender: '여', name: '' })
  const [sajuResult, setSajuResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [orderOpen, setOrderOpen] = useState(false)

  const go = (n) => setScreen(Math.max(0, Math.min(7, n)))
  const specs = sajuResult ? spoSpecs(sajuResult) : spoSpecs(null)
  const isDesktop = useIsDesktop()

  // 모바일 스포화면 swipe 제스처 + 최초 1회 코치마크 — 출처: 디자인봇 gate:spo_nav 목업(spo_nav_mobile.html)
  const [dragX, setDragX] = useState(0)
  const [dragging, setDragging] = useState(false)
  const touchStartX = useRef(0)
  const [coachSeen, setCoachSeen] = useState(() => {
    try { return localStorage.getItem('gosam_spo_swipe_coach_seen') === '1' } catch { return true }
  })
  const chipbarRef = useRef(null)

  useEffect(() => {
    if (screen !== 3 || coachSeen) return
    const t = setTimeout(() => {
      setCoachSeen(true)
      try { localStorage.setItem('gosam_spo_swipe_coach_seen', '1') } catch { /* noop */ }
    }, 1500)
    return () => clearTimeout(t)
  }, [screen, coachSeen])

  useEffect(() => {
    if (!chipbarRef.current) return
    const active = chipbarRef.current.querySelector('.spochip.active')
    if (active) active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }, [screen])

  const onSpoTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; setDragging(true) }
  const onSpoTouchMove = (e) => {
    const dx = e.touches[0].clientX - touchStartX.current
    setDragX(Math.max(-120, Math.min(120, dx)))
  }
  const onSpoTouchEnd = () => {
    if (dragX <= -60 && screen < 6) go(screen + 1)
    else if (dragX >= 60 && screen > 3) go(screen - 1)
    setDragging(false)
    setDragX(0)
  }

  const submitInput = async () => {
    if (!form.year || !form.month || !form.day) { setError('생년월일을 입력해 주세요'); return }
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API}/saju`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: +form.year, month: +form.month, day: +form.day,
          hour: form.hour ? +form.hour : null, gender: form.gender,
        }),
      })
      if (!res.ok) throw new Error('서버 응답 오류')
      const data = await res.json()
      setSajuResult(data)
      go(3)
    } catch (e) {
      setError('사주 계산에 실패했습니다. 잠시 후 다시 시도해 주세요.')
    } finally { setLoading(false) }
  }

  if (screen === 0 && isDesktop) {
    return (
      <div className="funnel-root">
        <PcIntroScreen onEnter={() => go(1)} onBack={() => {}} />
      </div>
    )
  }

  if (screen === 0 && !isDesktop) {
    return (
      <div className="funnel-root">
        <MobileIntroScreen onEnter={() => go(1)} />
      </div>
    )
  }

  // PC 와이드 화면(선택·입력·스포·페이월) — 출처: funnel_pc_screens.html (gate:gosam_pc_screens 등 7/7)
  if (isDesktop) {
    if (screen === 1) {
      return (
        <div className="funnel-root">
          <PcWide onBack={() => go(0)}>
            <span className="ey">무엇이 궁금하십니까</span>
            <div className="htitle">세 개의 <span className="r">문</span> 앞에 서 계십니다</div>
            <div className="hdesc">고르시는 문 안의 스포부터, 바로 보여드립니다.</div>
            <div className="tiles">
              {PC_TILES.map(t => (
                <button key={t.id} className="tile" onClick={() => t.id === 'tarot' ? onSelectTarot?.() : go(2)}>
                  <div className="thumb" style={{ backgroundImage: `url('${t.img}')` }} />
                  <div className="foot"><h3 className="serif">{t.h3}</h3><p>{t.desc}</p><span className="go">들어가기 ›</span></div>
                </button>
              ))}
            </div>
          </PcWide>
        </div>
      )
    }
    if (screen === 2) {
      return (
        <div className="funnel-root">
          <PcWide onBack={() => go(1)}>
            <span className="ey">당신을 알려 주십시오</span>
            <div className="htitle" style={{ fontSize: 38, marginBottom: 26 }}>당신 <span className="g">사주의 문</span>을 열 열쇠입니다</div>
            <div className="panel">
              <div className="field"><label>태어난 날</label>
                <div className="row2">
                  <input className="inp" placeholder="년(YYYY)" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} />
                  <input className="inp" placeholder="월" value={form.month} onChange={e => setForm({ ...form, month: e.target.value })} />
                  <input className="inp" placeholder="일" value={form.day} onChange={e => setForm({ ...form, day: e.target.value })} />
                </div>
              </div>
              <div className="field"><label>태어난 시간 (모르면 비워두세요)</label>
                <input className="inp" placeholder="예) 14 (24시간제, 모르면 비움)" value={form.hour} onChange={e => setForm({ ...form, hour: e.target.value })} />
              </div>
              <div className="field"><label>성별</label>
                <select className="inp" value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}>
                  <option value="여">여</option><option value="남">남</option>
                </select>
              </div>
              <div className="field"><label>이름 (부르는 이름)</label>
                <input className="inp" placeholder="예) 지현" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
              </div>
              {error && <div style={{ color: '#e08080', fontSize: 13, marginBottom: 12 }}>{error}</div>}
              <button className="cta serif" disabled={loading} onClick={submitInput}>
                {loading ? '신당에 올리는 중…' : '신당에 올리기'}
                <small>올리시는 순간, 스포가 시작됩니다</small>
              </button>
            </div>
          </PcWide>
        </div>
      )
    }
    if (screen >= 3 && screen <= 6) {
      const spec = specs[screen - 3]
      return (
        <div className="funnel-root">
          <PcWide onBack={() => go(2)} center onPrev={() => go(screen - 1)} onNext={() => go(screen + 1)}
            prevDisabled={screen === 3} nextDisabled={false}>
            <div className="spo">
              <div className="graphbox">
                <span className="spobadge">{spec.ico} {spec.badge}</span>
                <Graph pts={spec.pts} peakX={spec.peakX} color={spec.color} />
                <div className="spoyrs">{spec.yrs.map(y => <span key={y}>{y}</span>)}</div>
                <div className="spoline serif"><span className="hl">{spec.hl}</span> {spec.rest}</div>
              </div>
              <div className="reading">{spec.reading}
                <div className="lock">🔒 가려진 핵심(연도·달·상대·액수)은 신당 안에서 다 보여드립니다</div>
              </div>
            </div>
            <div className="sponavbar">
              <button className="sponavbtn prev" disabled={screen === 3} onClick={() => go(screen - 1)}>‹ 이전</button>
              <div className="sposegs">
                {specs.map((s, i) => (
                  <button key={s.badge} className={`sposeg${i === screen - 3 ? ' active' : i < screen - 3 ? ' done' : ''}`} onClick={() => go(3 + i)}>
                    <span className="ic">{s.ico}</span>{s.badge}
                  </button>
                ))}
              </div>
              <button className="sponavbtn next" onClick={() => go(screen + 1)}>{screen < 6 ? '다음 운세 ›' : '전체 결과 보기 ›'}</button>
            </div>
            <div className="navhint">키보드 ← → · 마우스 휠 · 위 칩 클릭 — 어느 방법으로도 넘기실 수 있습니다</div>
          </PcWide>
        </div>
      )
    }
    if (screen === 7) {
      return (
        <div className="funnel-root">
          <PcWide onBack={() => go(6)}>
            <span className="ey">여기까지가 무료 스포입니다</span>
            <div className="htitle" style={{ fontSize: 36, marginBottom: 26 }}>정확한 <span className="g">연도</span>와 전체 풀이는 신당 <span className="r">안에서</span></div>
            <div className="hdesc" style={{ marginBottom: 18 }}>언제·얼마나·어떻게. 흐릿한 건 제가 다 걷어 드립니다.</div>
            <div className="locked"><div className="blur">2026년 O월, 재물문이 크게 열리고 / 연애는 O월부터 신호가… / 결혼 적기는 20XX…</div><div className="ov">🔒</div></div>
            <div className="pricebox"><div className="p">₩ 9,900</div><div className="pn">4대 운(대박·조심·연애·결혼) 정확 연도 + 전체 풀이 · 완성 PDF 배달</div></div>
            <button className="cta serif" style={{ width: 520 }} onClick={() => setOrderOpen(true)}>전체 풀이 받기<small>무통장 안전결제 · 24시간 내 배달</small></button>
            <button className="pcback" onClick={() => go(0)}>처음으로 돌아가기</button>
          </PcWide>
          <OrderModal open={orderOpen} onClose={() => setOrderOpen(false)} productKey="saju4" amount={9900} productName="사주 4대운 전체 풀이" defaultName={form.name} />
        </div>
      )
    }
  }

  return (
    <div className="funnel-root">
      <TheaterFrame screen={screen} total={8} onPrev={() => go(screen - 1)} onNext={() => go(screen + 1)}>
      <div className="ph">
        {screen === 1 && (
          <>
            <div className="stage" /><div className="texture" /><div className="ambient" />
            <Top onBack={() => go(0)} />
            <div className="frameborder" /><div className="seal" style={{ right: 26, top: 92 }}>❖</div>
            <div className="content">
              <span className="ey">무엇이 궁금하십니까</span>
              <div className="htitle">세 개의 <span className="r">문</span> 앞에<br />서 계십니다</div>
              <div className="hdesc">고르시는 문 안의 스포부터, 바로 보여드립니다.</div>
              {TILES.map(t => (
                <button key={t.id} className="tile" style={{ backgroundImage: `url('${t.img}')` }}
                  onClick={() => t.id === 'tarot' ? onSelectTarot?.() : go(2)}>
                  <div className="tsc" />
                  <div className="tmeta"><h3>{t.title}</h3><p>{t.desc}</p></div>
                  <span className="tarw">들어가기 ›</span>
                </button>
              ))}
              <div className="subline" style={{ marginTop: 4 }}>어느 문 앞에 서시겠습니까</div>
            </div>
          </>
        )}

        {screen === 2 && (
          <>
            <div className="stage" /><div className="texture" />
            <Top onBack={() => go(1)} />
            <div className="frameborder" /><div className="seal" style={{ right: 26, top: 92 }}>❖</div>
            <div className="content">
              <span className="ey">당신을 알려 주십시오</span>
              <div className="htitle">당신 <span className="g">사주의 문</span>을<br />열 열쇠입니다</div>
              <div className="hdesc">거짓 없이 적으셔야, 신이 바로 읽습니다.</div>
              <div className="field"><label>태어난 날</label>
                <div className="row2">
                  <input className="inp" placeholder="년(YYYY)" value={form.year} onChange={e => setForm({ ...form, year: e.target.value })} />
                  <input className="inp" placeholder="월" value={form.month} onChange={e => setForm({ ...form, month: e.target.value })} />
                  <input className="inp" placeholder="일" value={form.day} onChange={e => setForm({ ...form, day: e.target.value })} />
                </div>
              </div>
              <div className="field"><label>태어난 시간 (모르면 비워두세요)</label>
                <input className="inp" placeholder="예) 14 (24시간제, 모르면 비움)" value={form.hour} onChange={e => setForm({ ...form, hour: e.target.value })} />
              </div>
              <div className="field"><label>성별</label>
                <select className="inp" value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}>
                  <option value="여">여</option><option value="남">남</option>
                </select>
              </div>
              <div className="field"><label>이름 (부르는 이름)</label>
                <input className="inp" placeholder="예) 지현" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
              </div>
              {error && <div style={{ color: '#e08080', fontSize: 13, marginBottom: 8 }}>{error}</div>}
              <div style={{ marginTop: 'auto' }}>
                <button className="cta" disabled={loading} onClick={submitInput}>
                  {loading ? '신당에 올리는 중…' : '신당에 올리기'}
                  <small>올리시는 순간, 스포가 시작됩니다</small>
                </button>
              </div>
            </div>
          </>
        )}

        {screen >= 3 && screen <= 6 && (() => {
          const spec = specs[screen - 3]
          const idx = screen - 3
          return (
            <>
              <div className="stage" /><div className="texture" /><div className="ambient" />
              <Top onBack={() => go(2)} />
              <div className="frameborder" />
              {/* 투명 tap존은 폐기 아닌 보조수단으로 유지(디자인봇 지시) — 주 수단은 아래 swipe+칩바+버튼 */}
              <div className="navzone left" onClick={() => go(screen - 1)} />
              <div className="navzone right" onClick={() => go(screen + 1)} />
              <div className="content">
                <div
                  className={`spocard${dragging ? ' dragging' : ''}`}
                  style={{ transform: `translateX(${dragX}px) rotate(${dragX / 60}deg)` }}
                  onTouchStart={onSpoTouchStart}
                  onTouchMove={onSpoTouchMove}
                  onTouchEnd={onSpoTouchEnd}
                >
                  <span className="spobadge">{spec.ico} {spec.badge}</span>
                  <div className="graph"><Graph pts={spec.pts} peakX={spec.peakX} color={spec.color} />
                    <div className="yrs">{spec.yrs.map(y => <span key={y}>{y}</span>)}</div>
                  </div>
                  <div className="spoline"><span className="hl">{spec.hl}</span> {spec.rest}</div>
                  <div className="reading">{spec.reading}</div>
                  <div className="lockline">🔒 ▓ 가려진 핵심(연도·달·상대·액수)은 신당 안에서 다 보여드립니다</div>
                  {dragX < -8 && screen < 6 && <div className="nextpeek" />}
                </div>
                <div className="spochipbar" ref={chipbarRef}>
                  {specs.map((s, i) => (
                    <button key={s.badge} className={`spochip${i === idx ? ' active' : i < idx ? ' done' : ''}`} onClick={() => go(3 + i)}>
                      {s.ico} {s.badge}
                    </button>
                  ))}
                </div>
                <div className="spomnav">
                  <button className="spomprev" disabled={screen === 3} onClick={() => go(screen - 1)}>‹</button>
                  <button className="spomnext" onClick={() => go(screen + 1)}>{screen < 6 ? '다음 운세 ›' : '전체 결과 보기 ›'}</button>
                </div>
              </div>
              {screen === 3 && !coachSeen && (
                <div className="spocoach">
                  <div className="box">
                    <div className="finger">👆</div>
                    <div className="txt"><b>밀어서</b> 다음 운세</div>
                  </div>
                </div>
              )}
            </>
          )
        })()}

        {screen === 7 && (
          <>
            <div className="stage" /><div className="texture" /><div className="ambient" />
            <Top onBack={() => go(6)} />
            <div className="frameborder" /><div className="seal" style={{ right: 26, top: 92 }}>❖</div>
            <div className="content">
              <span className="ey">여기까지가 무료 스포입니다</span>
              <div className="htitle">정확한 <span className="g">연도</span>와 전체 풀이는<br />신당 <span className="r">안에서</span></div>
              <div className="hdesc">언제·얼마나·어떻게. 흐릿한 건 제가 다 걷어 드립니다.</div>
              <div className="locked"><div className="blurcard">2026년 O월, 재물문이 크게 열리고 / 연애는 O월부터 신호가… / 결혼 적기는 20XX…</div><div className="lockover">🔒</div></div>
              <div className="pricebox"><div className="p">₩ 9,900</div><div className="pn">4대 운(대박·조심·연애·결혼) 정확 연도 + 전체 풀이</div><div className="mailrow">✉️ 완성 PDF, 이메일·카톡으로 배달</div></div>
              <button className="cta" onClick={() => setOrderOpen(true)}>전체 풀이 받기<small>무통장 안전결제 · 24시간 내 배달</small></button>
              <button className="subline" style={{ marginTop: 12, background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => go(0)}>처음으로 돌아가기</button>
            </div>
            <OrderModal open={orderOpen} onClose={() => setOrderOpen(false)} productKey="saju4" amount={9900} productName="사주 4대운 전체 풀이" defaultName={form.name} />
          </>
        )}
      </div>
      </TheaterFrame>
    </div>
  )
}
