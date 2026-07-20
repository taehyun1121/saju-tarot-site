import { useState, useEffect, useRef } from 'react'
import introVideo from '../assets/funnel/intro_pc_turnin.mp4'
import introPoster from '../assets/funnel/hall_wide_1.jpg'

// PC 전용 인트로(≥900px) — 배경 모션 영상(9s, 복도→신당진입→제단도착) 재생 후
// 0.7초 정지 여백 → 텍스트 슬라이드업+페이드인(0.6s). 텍스트는 영상에 안 굽고 실제 DOM.
// 출처: consulting/gosam_funnel/intro_pc_turnin.mp4 + txt_overlay.html (디자인봇 확정, gate:gosam_pc_texttiming 7/7)
// 🔴 모바일은 대상 아님(디자인봇: "모바일 9:16은 별도, 추후") — useIsDesktop()으로만 마운트됨.
export default function PcIntroScreen({ onEnter, onBack }) {
  const [textIn, setTextIn] = useState(false)
  const videoRef = useRef(null)

  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    const onEnded = () => { setTimeout(() => setTextIn(true), 700) }
    v.addEventListener('ended', onEnded)
    // 🔴 안전장치(2026-07-20, 실사용자 리포트로 추가): 브라우저 자동재생 정책·코덱·네트워크 등으로
    // 영상이 재생 자체가 안 되거나 'ended'가 영영 안 오면, 텍스트/CTA가 영원히 안 뜨고 사용자가 갇힘.
    // 영상 길이(9.13s)+정지여백(0.7s)보다 넉넉한 12초 후에는 무조건 텍스트를 띄운다(영상 상태 무관).
    const failsafe = setTimeout(() => setTextIn(true), 12000)
    return () => { v.removeEventListener('ended', onEnded); clearTimeout(failsafe) }
  }, [])

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'ArrowRight') onEnter() }
    const wheelLock = { current: false }
    const onWheel = (e) => {
      if (wheelLock.current || Math.abs(e.deltaY) < 20 || e.deltaY < 0) return
      wheelLock.current = true
      onEnter()
      setTimeout(() => { wheelLock.current = false }, 500)
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('wheel', onWheel)
    return () => { window.removeEventListener('keydown', onKey); window.removeEventListener('wheel', onWheel) }
  }, [onEnter])

  return (
    <div className="pcintro">
      <video ref={videoRef} className="pcintro-bg" src={introVideo} poster={introPoster}
        autoPlay muted playsInline preload="auto" />
      <div className="topscrim" /><div className="botscrim" /><div className="vign" />
      <div className="dancheong" />
      <div className="topbar"><button className="bk" onClick={onBack} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>‹</button><span className="wm serif">고삼<b>타로</b></span></div>
      <div className={`ui${textIn ? ' in' : ''}`}>
        <div className="chip">나를 마주할 자신이 있으시다면</div>
        <div className="head serif">오늘 밤, 당신의 <span className="g">운</span>의 문이<br />열립니다</div>
        <div className="desc">겁주는 점(占)이 아니라, 방향을 드립니다.</div>
        <button className="cta serif" onClick={onEnter}>지금 신당에 들어서기<small>무료 스포 · 정확한 건 신당 안에서 보여드립니다</small></button>
        <div className="footnote">방향키 · 스크롤로 다음 문으로 들어가십시오</div>
      </div>
    </div>
  )
}
