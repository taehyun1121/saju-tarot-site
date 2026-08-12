/* UnifiedPaywall — 사주 + 타로 통합 결론 페이월 (2026-08-11 신설)
 *
 * 🔴 왜 컴포넌트로 뽑았나
 *   지금 페이월이 **4벌**로 흩어져 있다:
 *     · TarotFunnelPage 모바일 318행 (.blurcard / .lockover)
 *     · TarotFunnelPage PC     424행 (.blur / .ov)
 *     · SajuFunnelPage 모바일·PC (각각 또 다른 클래스)
 *   같은 화면인데 클래스가 갈려서 **한쪽만 고쳐지는 사고가 반복됐다**
 *   (2026-08-11 PC 시안 누락·CTA 라운드 불일치가 전부 이 구조에서 났다).
 *   → 한 벌로 합치고 모바일/PC는 CSS(900px 미디어쿼리)로만 가른다.
 *
 * 🔴 형 결정 반영
 *   · "타로랑 사주를 합쳐보는 걸로" → 상품까지 합침. 두 축을 한 화면에 수렴시킨다.
 *   · "가린 A안으로 가자" → 무료는 **실제 산출값을 그대로 공개**하고 핵심 토큰만 가린다.
 *     가짜 자리표시자("2026년 O월…") 폐기 — 걷어도 내용이 없는 빈 껍데기는 신뢰를 깎는다.
 *
 * 🔴 소프트 페이월 방식 (외부 실측 근거)
 *   업계 표준은 **전문을 다 내려보내고 화면에서만 가리는 것**이다. 그래야 크롤러가 전문을 읽는다
 *   (구글은 페이월 콘텐츠 전용 정책이 있어 클로킹으로 보지 않는다).
 *   → props로 받는 텍스트는 **전문**이고, 가리는 건 <Rd>로 감싼 토큰뿐이다.
 *     DOM에서 잘라내지 않는다.
 */
import OrderModal from './OrderModal'
import PromoBanner from './PromoBanner'

const Rd = ({ children }) => <span className="rd">{children}</span>

/** 실산출 문장에서 핵심 토큰만 가린다.
 *  🔴 기존 방식(문장을 45% 지점에서 잘라 뒤를 통째로 블러)은 "값을 안 준다"는 인상만 남긴다.
 *     A안은 **문장은 읽히되 결정적 값(연도·달·상대·수치)만** 가리는 것이라 토큰 단위로 처리한다.
 *  · 백엔드가 `redact` 배열(가릴 토큰)을 주면 그걸 쓰고,
 *  · 없으면 패턴(N월·N년·N세·숫자+단위)으로 잡는다. 못 잡으면 그냥 다 보여준다 —
 *    **가짜로 지어내서 가리는 것보다 덜 가리는 게 낫다.**
 */
const TOKEN_RE = /(\d{1,2}월|\d{4}년|\d{1,2}세|\d+(?:,\d{3})*원)/g

export function Redacted({ text, tokens }) {
  if (!text) return null
  const marks = (tokens && tokens.length) ? tokens : (text.match(TOKEN_RE) || [])
  if (!marks.length) return <>{text}</>
  // 가장 긴 토큰부터 잘라야 부분매칭으로 어긋나지 않는다
  const sorted = [...new Set(marks)].sort((a, b) => b.length - a.length)
  const re = new RegExp(`(${sorted.map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g')
  return (
    <>
      {text.split(re).map((part, i) =>
        sorted.includes(part) ? <Rd key={i}>{part}</Rd> : <span key={i}>{part}</span>
      )}
    </>
  )
}

/**
 * @param {object}  saju        사주 축 — { text, tokens }  (무료 전체공개)
 * @param {object}  tarot       타로 축 — { cardName, text, tokens }  (첫 장만 무료)
 * @param {object}  merge       통합 결론 — { text, tokens }  (유료)
 * @param {array}   locked      잠긴 목차 [{ title, open }]
 * @param {number}  amount      가격. 🔴 2026-08-12 형 확정: "고삼타로 서비스 가격 9,900원"
 *                              (사주/타로/통합 나누지 않고 전부 9,900). 기본값 9900.
 * @param {string}  productKey  결제 상품 키
 */
export default function UnifiedPaywall({
  saju, tarot, merge, locked = [], amount = 9900,
  productKey = 'unified', productName = '사주 x 카드 합친 결론',
  readingData = null, defaultName = '', orderOpen, setOrderOpen, onBack,
}) {
  return (
    <>
      <span className="ey">두 개가 같은 걸 가리켰어</span>
      <div className="htitle">
        <span className="g">사주 × 카드</span>,<br />합친 결론은 <span className="r">여기서</span>
      </div>

      {/* 사주축 — 무료 전체공개. 원가 0이라 크게 풀어도 손해가 없고, 크롤러가 읽을 본문이 된다 */}
      {saju && (
        <div className="axis saju">
          <div className="h">🪔 사주가 보는 큰 흐름 <span className="free">· 무료</span></div>
          <p><Redacted text={saju.text} tokens={saju.tokens} /></p>
        </div>
      )}

      {/* 타로축 — 첫 장만 무료. 뽑아야 나오는 희소재라 여기서부터 값을 잠근다 */}
      {tarot && (
        <div className="axis tarot">
          <div className="h">🔮 카드가 짚는 지금 <span className="free">· 첫 장 무료</span></div>
          <p>
            {tarot.cardName && <>첫 장은 <b>'{tarot.cardName}'</b> — </>}
            <Redacted text={tarot.text} tokens={tarot.tokens} />
          </p>
        </div>
      )}

      {/* 수렴 — 두 축이 같은 곳을 가리킨다는 것이 이 상품의 논거다 */}
      <div className="conv">↓ 두 축이 같은 곳을 가리킨다 = 그래서</div>

      {/* 통합 결론 — 유료. 여기가 실제로 파는 것 */}
      {merge && (
        <div className="axis merge">
          <div className="h">✦ 통합 결론 <span className="free">· 유료</span></div>
          <p><Redacted text={merge.text} tokens={merge.tokens} /></p>
          <div className="ufade" />
        </div>
      )}

      {/* 잠긴 목차 — 무엇이 잠겼는지 제목으로 보여준다. 빈 블러보다 가치가 드러난다 */}
      {locked.length > 0 && (
        <div className="utoc">
          {locked.map((it, i) => (
            <div className="row" key={i}>
              <span className="t">{i + 1}. {it.title}</span>
              {it.open ? <span className="v">맛보기 열림 ✓</span> : <span className="lk">🔒</span>}
            </div>
          ))}
        </div>
      )}

      <PromoBanner />

      <div className="pricebox">
        {/* 🔴 통합가는 형 영역이다. 안 정해졌으면 지어내지 않고 자리만 비운다 */}
        <div className="p">{amount ? `₩ ${amount.toLocaleString()}` : '₩ —'}</div>
        <div className="pn">
          {amount ? '잠긴 항목 전체 + 완성 PDF 배달' : '통합가 확정 예정 · 완성 PDF 배달'}
        </div>
      </div>

      <button className="cta" disabled={!amount} onClick={() => setOrderOpen(true)}>
        사주 × 카드 합친 결론 열기
        <small>무통장 안전결제 · 24시간 내 배달</small>
      </button>

      {onBack && (
        <button className="subline" style={{ marginTop: 12, background: 'none', border: 'none', cursor: 'pointer' }}
                onClick={onBack}>처음으로 돌아가기</button>
      )}

      <div className="note" style={{ marginTop: 12 }}>
        🔴 가린 부분은 <b>실제 산출값의 핵심 토큰만</b> 가린 것(가짜 문장·빈 껍데기 아님).
        전문은 서버가 다 내려주고 화면에서만 가린다.
      </div>

      {amount && (
        <OrderModal open={orderOpen} onClose={() => setOrderOpen(false)}
                    productKey={productKey} amount={amount} productName={productName}
                    defaultName={defaultName} readingData={readingData} />
      )}
    </>
  )
}
