import { useEffect, useRef } from 'react'
import imgShrineHero from '../assets/funnel/hb_A_hall.jpg'

// PC 데스크탑 전용 "극장형" 배경 프레임 — 900px 이상에서만 보임(모바일은 그대로 .ph 단독 렌더).
// 출처: consulting/gosam_funnel/funnel_pc_blue.html (디자인봇 확정, gate:gosam_pc_theater 7/7)
// children = 기존 .ph 화면(SajuFunnelPage/TarotFunnelPage 공용) 그대로 재사용, 여기선 감싸는 배경/네비만 추가.
export default function TheaterFrame({ screen, total, onPrev, onNext, bgPos, children }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowLeft') onPrev()
      else if (e.key === 'ArrowRight') onNext()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onPrev, onNext])

  const wheelLock = useRef(false)
  const onWheel = (e) => {
    if (wheelLock.current || Math.abs(e.deltaY) < 20) return
    wheelLock.current = true
    if (e.deltaY > 0) onNext(); else onPrev()
    setTimeout(() => { wheelLock.current = false }, 500)
  }

  return (
    <div className="theater" onWheel={onWheel}>
      <div className="hallbg" style={{ backgroundImage: `url('${imgShrineHero}')`, backgroundPosition: bgPos || 'center 32%' }} />
      <div className="hallscrim" />
      <div className="dancheong" />
      <div className="tframe" />
      <div className="ttitle"><div className="wm">고삼<b>타로</b></div><div className="sub">고 풍 몰 입 · 극 장 형 (P C)</div></div>
      <div className="nav l" onClick={onPrev}><div className="arw">‹</div><div className="lb">이전</div></div>
      <div className="nav r" onClick={onNext}><div className="arw">›</div><div className="lb">다음</div></div>
      <div className="phwrap">{children}</div>
      <div className="thint">
        ← 방향키 · 스크롤 · 화살표로 넘기십시오 →
        <span className="dots">{Array.from({ length: total }, (_, i) => <i key={i} className={i === screen ? 'on' : ''} />)}</span>
      </div>
    </div>
  )
}
