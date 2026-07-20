import { useEffect, useRef } from 'react'

// 카드뽑기 화면(.fan) 진입 시 1회 재생되는 리플셔플→딜 애니메이션.
// 출처: consulting/gosam_funnel/funnel_shuffle_anim.html (디자인봇 확정, gate:gosam_shuffle_anim 7/7)
//   Web Animations API 키프레임 구조(스플릿→리플→컷→딜) 그대로 이식, 거리값만 우리 .fan 실제 폭(모바일 좁은 화면)에 맞게 축소.
// 최종 정착 위치는 fanTransform(i)로 기존 클릭형 부채꼴과 완전히 동일 — 애니메이션 끝나도 히트박스 안 어긋남.
export default function ShuffleFan({ n, fanTransform, onDraw, drawing }) {
  const cardRefs = useRef([])

  useEffect(() => {
    const anims = cardRefs.current.map((el, i) => {
      if (!el) return null
      const side = i % 2 === 0 ? -1 : 1
      const final = fanTransform(i)
      const kf = [
        { transform: 'translate(0,0) rotate(0deg)', offset: 0 },
        // 1) 스플릿 — 두 뭉치로 갈라짐
        { transform: `translate(${side * 42}px,8px) rotate(${side * 7}deg)`, offset: .18 },
        { transform: `translate(${side * 42}px,8px) rotate(${side * 7}deg)`, offset: .24 },
        // 2) 리플 — 아치 그리며 중앙으로 촤라락
        { transform: `translate(${side * 18}px,-14px) rotate(${side * 3}deg)`, offset: .36 },
        { transform: 'translate(0,0) rotate(0deg)', offset: .5 },
        // 3) 한 번 더 컷(브릿지 느낌 미세 흔들림)
        { transform: `translate(${side * 8}px,-5px) rotate(${side * 2}deg)`, offset: .58 },
        { transform: 'translate(0,0) rotate(0deg)', offset: .66 },
        { transform: 'translate(0,0) rotate(0deg)', offset: .72 },
        // 4) 딜 — 부채꼴 자리로 날아가 배치(기존 클릭형 fanTransform과 동일 최종 위치)
        { transform: final, offset: 1 },
      ]
      return el.animate(kf, { duration: 3400, delay: i * 26, fill: 'both', easing: 'cubic-bezier(.4,0,.25,1)' })
    })
    return () => anims.forEach(a => a && a.cancel())
  }, [n, fanTransform])

  return (
    <div className="fan" onClick={drawing ? undefined : onDraw} style={{ cursor: drawing ? 'default' : 'pointer' }}>
      {Array.from({ length: n }, (_, i) => (
        <div key={i} ref={el => (cardRefs.current[i] = el)} className="cardback" />
      ))}
    </div>
  )
}
