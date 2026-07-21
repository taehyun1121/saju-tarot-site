import { useState, useEffect, useRef } from 'react'
import introVideo from '../assets/funnel/intro_mobile_turnin.mp4'
import introPoster from '../assets/funnel/hb_A_hall.jpg'

// 모바일 전용 인트로(<900px) — PC 인트로(PcIntroScreen)와 동일 컨셉 통일
// (디자인봇 벤치마킹 근거: Awwwards/3D 사이트 관례상 데스크톱·모바일은 같은 인트로 컨셉이 정석).
// 배경 세로영상(4.04s, 정자살 창·측벽→제단 스윕) 재생 후 0.7초 정지여백 → 텍스트 페이드인.
// 텍스트는 영상에 안 굽고 실제 DOM(PC와 동일 원칙).
// 출처: consulting/gosam_funnel/intro_i2v_mobile_trim_web.mp4 (디자인봇, 원본 5초 중 1~5초 구간만 트림 확정)
export default function MobileIntroScreen({ onEnter }) {
  const [textIn, setTextIn] = useState(false)
  const videoRef = useRef(null)

  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    const onEnded = () => { setTimeout(() => setTextIn(true), 700) }
    v.addEventListener('ended', onEnded)
    // PC와 동일한 안전장치: 영상 길이(4.04s)+정지여백보다 넉넉한 7초 후엔 무조건 텍스트 노출
    const failsafe = setTimeout(() => setTextIn(true), 7000)
    return () => { v.removeEventListener('ended', onEnded); clearTimeout(failsafe) }
  }, [])

  // 🔴 코코 추가(2026-07-21, 실사용자 피드백): iOS 저전력 모드는 autoplay를 OS 정책으로 강제 차단
  // (muted/playsInline 다 넣어도 못 뚫음, 웹표준에 우회 API 없음) — 대신 "사용자 제스처가 있으면"
  // 재생은 허용되므로, 화면 아무 곳이나 첫 터치/클릭에 바로 재생을 시도해 체감 지연을 최소화.
  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    const tryPlay = () => { if (v.paused) v.play().catch(() => {}) }
    document.addEventListener('touchstart', tryPlay, { once: true, passive: true })
    document.addEventListener('click', tryPlay, { once: true })
    return () => {
      document.removeEventListener('touchstart', tryPlay)
      document.removeEventListener('click', tryPlay)
    }
  }, [])

  return (
    <div className="ph mobintro">
      <video ref={videoRef} className="mobintro-bg" src={introVideo} poster={introPoster}
        autoPlay muted playsInline preload="auto" />
      <div className="scrim" />
      <div className="dancheong" />
      <div className="top"><span className="wm" style={{ color: '#f3e7d2' }}>고삼<b style={{ color: '#e3c069' }}>타로</b></span></div>
      <div className="seal" style={{ left: 24, top: 96 }}>❖</div>
      <div className={`bottom${textIn ? ' in' : ''}`}>
        <div className="chip">나를 마주할 자신이 있으시다면</div>
        <div className="introcard">
          <div className="ihead">오늘 밤, 당신의<br /><span className="g">운</span>의 문이 열립니다</div>
          <div className="idesc">겁주는 점(占)이 아니라, 방향을 드립니다.</div>
        </div>
        <button className="cta" onClick={onEnter}>지금 신당에 들어서기<small>무료 스포 · 정확한 건 안에서 보여드립니다</small></button>
      </div>
    </div>
  )
}
