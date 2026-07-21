import { useState, useEffect, useRef } from 'react'
import { API } from '../api'

// 오픈이벤트(1+1) 진입 팝업 — 디자인봇 event_modal_pc/mobile.html 이식(2026-07-21).
// 출처: consulting/gosam_funnel/event_modal_pc.html · event_modal_mobile.html
// (디자인봇 확정, 형 ㄱㄱ). 오퍼값(1+1) 스타 위계 + 혜택3 + 자동적용 배지(쿠폰코드 없음).
// 등장 조건(디자인봇 권고): 최초진입 즉시 노출은 이탈률↑ → 6초 지연 또는 데스크톱 이탈의도(마우스가
// 뷰포트 상단 밖으로 나감) 중 먼저 오는 쪽에 노출, 이후 닫으면(X·CTA·"다음에 볼게요" 전부) localStorage로
// 이 프로모(ends_at 기준) 재노출 차단 — 새 프로모가 뜨면(ends_at이 바뀌면) 자동으로 다시 보여줄 수 있음.
const SEEN_KEY_PREFIX = 'gosam_event_modal_seen_'

export default function EventModal() {
  const [promo, setPromo] = useState(null)
  const [visible, setVisible] = useState(false)
  const [now, setNow] = useState(() => Date.now())
  // 🔴 코코 수정(2026-07-21, 실사용자 리포트 "끄면 좀 있으면 뜨고"): dismiss()가 localStorage만
  // 기록하고 이미 예약된 6초 타이머·이탈의도 리스너는 안 지워서, 닫은 뒤에도 그게 나중에 발화해
  // setVisible(true)를 다시 불러버렸음 — ref로 "닫힘" 상태를 콜백 시점에도 확인하도록 수정.
  const dismissedRef = useRef(false)

  useEffect(() => {
    let alive = true
    fetch(`${API}/promo`).then(r => r.json()).then(d => { if (alive) setPromo(d) }).catch(() => {})
    return () => { alive = false }
  }, [])

  const seenKey = promo?.ends_at ? `${SEEN_KEY_PREFIX}${promo.ends_at}` : null
  const alreadySeen = seenKey ? (() => { try { return localStorage.getItem(seenKey) === '1' } catch { return false } })() : true

  useEffect(() => {
    if (!promo?.active || !promo.ends_at || alreadySeen) return
    const showIfNotDismissed = () => { if (!dismissedRef.current) setVisible(true) }
    const timer = setTimeout(showIfNotDismissed, 6000)
    const onExitIntent = (e) => { if (e.clientY <= 0) showIfNotDismissed() }
    document.addEventListener('mouseleave', onExitIntent)
    return () => { clearTimeout(timer); document.removeEventListener('mouseleave', onExitIntent) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [promo?.active, promo?.ends_at])

  useEffect(() => {
    if (!visible) return
    const t = setInterval(() => setNow(Date.now()), 60000)
    return () => clearInterval(t)
  }, [visible])

  const dismiss = () => {
    dismissedRef.current = true
    setVisible(false)
    if (seenKey) { try { localStorage.setItem(seenKey, '1') } catch { /* noop */ } }
  }

  if (!visible || !promo?.active || !promo.ends_at) return null
  const remainMs = new Date(promo.ends_at).getTime() - now
  if (remainMs <= 0) return null
  const d = Math.floor(remainMs / 86400000)
  const h = Math.floor((remainMs % 86400000) / 3600000)

  return (
    <div className="evtmodal-stage" onClick={dismiss}>
      <div className="evtmodal-modal" onClick={(e) => e.stopPropagation()}>
        <div className="evtmodal-dan" />
        <button className="evtmodal-x" onClick={dismiss} aria-label="닫기">✕</button>
        <div className="evtmodal-body"><div className="evtmodal-inner">
          <div className="evtmodal-badge">❖ 1+1 이벤트 · 진행 중</div>
          <div className="evtmodal-head serif">한 번의 물음에<br /><b>두 개의 답</b>을 드립니다</div>
          <div className="evtmodal-sub">지금 청하시면, 주문 한 건에 결과 두 건을 보여드립니다.</div>

          <div className="evtmodal-offer">
            <div className="pct">1<span className="off">+</span>1</div>
            <div className="cap">결과 하나 값에, <b style={{ color: 'var(--gold)' }}>둘</b></div>
            <div className="price">한 건 결제 <b>9,900원</b> → <b style={{ color: 'var(--gold)' }}>리딩 2건 제공</b></div>
          </div>

          <div className="evtmodal-benefits">
            <div className="brow"><span className="ic">✓</span><span className="tx">결과 <b style={{ color: 'var(--gold)' }}>2건</b> 제공 — 한 건 값으로<small>사주·타로 전 상품 적용</small></span></div>
            <div className="brow"><span className="ic">✓</span><span className="tx">두 번째 결과 자동 포함<small>따로 결제·코드 입력 필요 없음</small></span></div>
            <div className="brow"><span className="ic">✓</span><span className="tx">이벤트 기간 한정<small>종료 후에는 사라집니다</small></span></div>
          </div>

          <div className="evtmodal-coupon">
            <div style={{ fontSize: 22 }}>🎁</div>
            <div style={{ textAlign: 'left' }}>
              <div className="lab">코드 입력 불필요</div>
              <div className="txt">결제 시 결과 2건이 자동으로 담깁니다</div>
            </div>
          </div>

          <button className="evtmodal-cta" onClick={dismiss}>1+1로 시작하기</button>
          <div className="evtmodal-limit"><span className="dot">●</span> 이벤트 종료까지 <b>{d}일 {h}시간</b></div>
          <div className="evtmodal-later" onClick={dismiss}>다음에 볼게요</div>
        </div></div>
      </div>
    </div>
  )
}
