import { useEffect, useRef, useState } from 'react'
import { API } from '../api'

// 상품 3단 (시안: VIP 앵커 상단 / 3영역 종합 BEST / 집중). key는 백엔드 계약값이라 유지.
const PRODUCTS = [
  { key: 'premium', name: 'VIP 종합', price: 45000, emoji: '📜',
    desc: '5영역 전부 + 대운 10년 + 1:1 코멘트',
    features: ['시기 로드맵 + 대운 10년', '맞춤 처방(용신) + 궁합 심층 + 택일', '전문가 1:1 해설 코멘트'] },
  { key: 'package', name: '3영역 종합', price: 25000, original: 33000, emoji: '✨', best: true,
    desc: '핵심 3가지 깊이 · PDF 해설집',
    features: ['시기 로드맵 (킬러 콘텐츠)', '맞춤 처방(용신)', '궁합 심층 또는 택일 (택1)'] },
  { key: 'single', name: '집중 리딩', price: 15000, emoji: '🔮',
    desc: '가장 궁금한 1영역만 · 핵심만 빠르게',
    features: ['시기 로드맵 · 궁합 · 택일 중 택1', '핵심만 빠르게'] },
  { key: 'compat', name: '궁합보기', price: 26000, emoji: '💞',
    desc: '두 사람 사주로 보는 관계 궁합 (상대방 사주까지 함께)',
    features: ['두 사람 오행 궁합 — 상생·상극', '시기별 관계 온도 — 언제 가까워지고 멀어지는지', '궁합 점수 + 관계 조언'] },
]

// 유료 가치 5가지 ("지도") — 시안 ③
const VALUES = [
  { icon: '🗺️', tag: 'KILLER', title: '시기 로드맵', desc: '올해~3년, 언제 이직·연애·투자가 열리고 닫히는지 월 단위 흐름표.' },
  { icon: '📈', title: '대운 10년', desc: '지금 들어와 있는 10년 대운의 성격과 남은 기간 — 큰 판의 방향.' },
  { icon: '🌿', title: '맞춤 처방(용신)', desc: '부족한 기운을 채우는 색·방향·직업·습관 — "무엇을 하면 되는지".' },
  { icon: '💞', title: '궁합 심층', desc: '상대 사주와의 오행 상생/상극, 시기별 관계 온도.' },
  { icon: '📅', title: '택일', desc: '계약·이사·개업·고백 — 나에게 맞는 좋은 날 콕 집기.' },
]

// 결제·받아보기 3스텝 — 시안 ⑤ (실제 계좌는 주문 후 deposit 단계에서 백엔드가 안내)
const STEPS = [
  { n: '①', title: '상품 선택 후 무통장 입금', meta: '국민은행 · 신청 시 계좌 안내' },
  { n: '②', title: '입금 확인', meta: '보통 1~3시간 내' },
  { n: '③', title: '결과 전달', meta: 'PDF 해설집 (이메일/카톡)' },
]

// 상담받으신 분들의 반응 — 상담봇이 실제 상담 녹취 발화를 익명화(창작 아님). 정식 리뷰 아님 → 별점 없음, 주석 표기.
const REVIEWS = [
  { text: '다 맞아떨어진다기보다, 오래 붙잡고 있던 고민의 방향이 정리되는 느낌이었어요. 끝나고 나니 속이 확 시원했습니다.', who: '30대 직장인 여성 · 진로 상담' },
  { text: '고민을 차분히 짚어주셔서 마음이 한결 놓였어요. 감사했습니다.', who: '30대 자영업 여성 · 금전·사업 상담' },
  { text: '막막하던 상황을 하나씩 풀어서 봐주셔서 방향을 잡는 데 도움이 됐어요.', who: '30대 직장인 여성 · 재회 상담' },
]

const ORDER_KEY = 'saju-premium-order'

export default function PremiumPage() {
  const [step, setStep] = useState('select')      // select → form → deposit → done
  const [product, setProduct] = useState(null)
  const [form, setForm] = useState({ name: '', contact: '', question: '' })
  const [order, setOrder] = useState(null)        // 주문 생성 응답
  const [status, setStatus] = useState('pending')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const pollRef = useRef(null)
  // 무료(라이트) 결과 리캡 — 라이트 사이트가 남긴 값이 있으면 히어로 아래에 표시(없으면 섹션 숨김, 가짜값 안 씀).
  const [freeRecap] = useState(() => {
    try { return localStorage.getItem('saju-lite-recap') || '' } catch { return '' }
  })

  // 새로고침해도 진행 중 주문 복원
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(ORDER_KEY) || 'null')
      if (saved?.order_id) {
        setOrder(saved)
        setStep('deposit')
        refreshStatus(saved.order_id)
      }
    } catch { /* ignore */ }
    return () => clearInterval(pollRef.current)
  }, [])

  // 궁합보기(26000) 또는 VIP 종합(45000, 궁합 포함) 결제자 → SajuPage '대상 추가' 언락
  const unlockCompat = (amt) => {
    if (amt === 26000 || amt === 45000) {
      try { localStorage.setItem('saju-compat-unlocked', '1') } catch { /* ignore */ }
    }
  }

  const refreshStatus = async (orderId) => {
    try {
      const res = await fetch(`${API}/orders/${orderId}`)
      if (!res.ok) return
      const data = await res.json()
      setStatus(data.status)
      if (data.status === 'paid') {
        clearInterval(pollRef.current)
        unlockCompat(data.amount ?? order?.amount)
        setStep('done')
        localStorage.removeItem(ORDER_KEY)
      }
    } catch { /* ignore */ }
  }

  const createOrder = async () => {
    setError('')
    if (!form.name.trim()) return setError('입금하실 분 성함을 입력해주세요')
    if (!form.contact.trim()) return setError('결과 받으실 연락처(이메일/카톡ID)를 입력해주세요')
    setLoading(true)
    try {
      const res = await fetch(`${API}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product: product.key,
          buyer_name: form.name.trim(),
          contact: form.contact.trim(),
          question: form.question.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '주문 생성에 실패했습니다')
      setOrder(data)
      localStorage.setItem(ORDER_KEY, JSON.stringify(data))
      setStep('deposit')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const claimDeposit = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/orders/${order.order_id}/claim`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '확인 요청에 실패했습니다')
      setStatus(data.status)
      if (data.status === 'paid') {
        unlockCompat(order?.amount ?? data.amount)
        setStep('done')
        localStorage.removeItem(ORDER_KEY)
      } else {
        // 입금 확인될 때까지 폴링 (5초 간격, 10분 한도)
        clearInterval(pollRef.current)
        let count = 0
        pollRef.current = setInterval(() => {
          if (++count > 120) return clearInterval(pollRef.current)
          refreshStatus(order.order_id)
        }, 5000)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const resetAll = () => {
    clearInterval(pollRef.current)
    localStorage.removeItem(ORDER_KEY)
    setOrder(null); setProduct(null); setStatus('pending'); setError('')
    setForm({ name: '', contact: '', question: '' })
    setStep('select')
  }

  const inputCls = 'bg-app-input border border-p-600 rounded-lg px-3 py-2 text-p-10 text-sm outline-none focus:border-p-300 placeholder:text-[#4a3870] w-full'

  return (
    <div className="max-w-[720px] mx-auto flex flex-col gap-5">
      {/* 폼/입금/완료 단계에서만 컴팩트 헤더. select 단계는 아래 전환 랜딩의 히어로가 대신함. */}
      {step !== 'select' && (
        <div className="text-center">
          <h2 className="text-gold text-xl font-bold mb-1">💎 심층 리포트</h2>
          <p className="text-p-200 text-sm">무료 풀이에서 못 다룬 시기 · 구체 조언까지 — 전 단계 <b className="text-gold">PDF 해설집</b>으로 보내드립니다</p>
        </div>
      )}

      {step === 'select' && (
        <div className="flex flex-col gap-10">

          {/* ① 히어로 — 자이가르닉 */}
          <section className="text-center pt-2">
            <span className="inline-block bg-app-card border border-gold/60 text-gold text-xs font-bold px-3 py-1 rounded-full mb-4">✓ 무료 풀이 완료</span>
            <h1 className="text-p-10 text-2xl font-extrabold leading-snug">
              타고난 기질은 봤습니다<br />
              <span className="text-gold">이제 언제·어떻게가 남았어요</span>
            </h1>
            <p className="text-p-200 text-sm mt-3 leading-relaxed">
              무료로 본 건 ‘나’라는 그림.<br />
              유료는 그 그림이 <b className="text-p-10">언제 어떻게 움직이는지</b>의 지도예요.
            </p>
            {freeRecap && (
              <div className="bg-app-card border border-p-600 rounded-xl px-4 py-3 mt-5 text-left">
                <div className="text-p-200 text-[11px] mb-1">방금 보신 나의 라이트 결과</div>
                <div className="text-p-10 text-sm leading-relaxed">{freeRecap}</div>
              </div>
            )}
            <a href="#pricing" className="inline-block text-gold text-xl mt-5 animate-bounce">⌄</a>
          </section>

          {/* ③ 유료 가치 = 지도 */}
          <section>
            <div className="text-p-200 text-xs font-bold tracking-wider mb-1">WHAT YOU GET</div>
            <h2 className="text-p-10 text-lg font-bold mb-1">유료는 ‘지도’입니다</h2>
            <p className="text-p-200 text-xs mb-4">타고난 기질(무료) 위에, 시기와 방법을 얹었어요. 각 항목은 이렇게 구체적으로 나와요.</p>
            <div className="flex flex-col gap-3">
              {VALUES.map(v => (
                <div key={v.title} className="flex gap-3 bg-app-card border border-p-600 rounded-xl p-4">
                  <div className="text-2xl leading-none shrink-0">{v.icon}</div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-p-10 font-bold text-sm">{v.title}</span>
                      {v.tag && <span className="bg-gold text-[#1a1030] text-[10px] font-extrabold px-1.5 py-0.5 rounded">{v.tag}</span>}
                    </div>
                    <p className="text-p-200 text-xs mt-1 leading-relaxed">{v.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ④ 상품 3단 — 가격 앵커링 */}
          <section id="pricing">
            <h2 className="text-p-10 text-lg font-bold mb-1">어디까지 펼쳐볼까요?</h2>
            <p className="text-p-200 text-xs mb-4">가장 많이 고르는 건 <b className="text-gold">3영역 종합</b>이에요.</p>
            <div className="flex flex-col gap-3">
              {PRODUCTS.map(p => (
                <button key={p.key} onClick={() => { setProduct(p); setStep('form') }}
                  className={`relative text-left bg-app-card border rounded-xl p-5 transition-all hover:border-p-300
                    ${p.best ? 'border-gold shadow-[0_0_0_1px_rgba(230,196,137,0.4)] bg-[#241f45]' : 'border-p-600'}`}>
                  {p.best && (
                    <span className="absolute -top-2.5 left-4 bg-gold text-[#1a1030] text-[11px] font-extrabold px-2.5 py-0.5 rounded-full">🔥 BEST · 가장 인기</span>
                  )}
                  <div className="flex items-start justify-between gap-3">
                    <div className="text-p-10 font-bold">{p.emoji} {p.name}</div>
                    <div className="text-right whitespace-nowrap">
                      {p.original && <div className="text-p-200 text-xs line-through">₩{p.original.toLocaleString()}</div>}
                      <div className="text-gold font-extrabold text-xl leading-none">₩{p.price.toLocaleString()}</div>
                    </div>
                  </div>
                  <p className="text-p-200 text-xs mt-1">{p.desc}</p>
                  <ul className="mt-3 flex flex-col gap-1.5">
                    {p.features.map(f => (
                      <li key={f} className="text-p-100 text-xs flex gap-1.5"><span className="text-gold">✓</span>{f}</li>
                    ))}
                  </ul>
                  <div className={`mt-4 text-center rounded-lg py-2.5 text-sm font-bold
                    ${p.best ? 'bg-[#e0a63a] text-[#241606]' : 'border border-p-500 text-p-100'}`}>
                    {p.name} 선택 →
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* ⑤ 결제·받아보기 + 신뢰 */}
          <section>
            <div className="text-p-200 text-xs font-bold tracking-wider mb-1">HOW IT WORKS</div>
            <h2 className="text-p-10 text-lg font-bold mb-4">결제 · 받아보기</h2>
            <div className="flex flex-col gap-2.5">
              {STEPS.map(s => (
                <div key={s.n} className="flex items-center gap-3 bg-app-card border border-p-600 rounded-lg px-4 py-3">
                  <span className="text-gold font-extrabold">{s.n}</span>
                  <span className="text-p-10 text-sm font-bold flex-1">{s.title}</span>
                  <span className="text-p-200 text-xs text-right">{s.meta}</span>
                </div>
              ))}
            </div>
            {/* 상담받으신 분들의 반응 — 실발화 익명화(정식 리뷰 아님, 별점 없음) */}
            <div className="mt-6">
              <div className="text-p-200 text-xs font-bold tracking-wider mb-2">상담받으신 분들의 반응</div>
              <div className="flex flex-col gap-2.5">
                {REVIEWS.map((r, i) => (
                  <div key={i} className="bg-app-card border border-p-600 rounded-xl p-4">
                    <p className="text-p-100 text-sm leading-relaxed">“{r.text}”</p>
                    <p className="text-p-200 text-xs mt-2">— {r.who}</p>
                  </div>
                ))}
              </div>
              <p className="text-p-200 text-[11px] mt-2">※ 실제 상담 종료 후 남기신 반응을 익명화해 옮긴 것입니다.</p>
            </div>

            <p className="text-p-200 text-[11px] text-center mt-4 leading-relaxed">
              무통장 안전결제 · 입금 확인 후 <b className="text-gold">24시간 내</b> PDF 해설집을 이메일/카톡으로 보내드려요.
            </p>
            <a href="#pricing" className="block text-center bg-p-400 border border-p-300 text-white font-bold rounded-lg py-3 text-sm mt-4 hover:bg-p-350">
              타고난 걸 봤다면, 이제 타이밍을 →
            </a>
          </section>

        </div>
      )}

      {step === 'form' && product && (
        <div className="bg-app-card border border-p-600 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="text-p-10 font-bold">{product.emoji} {product.name}</span>
            <span className="text-gold font-bold">₩{product.price.toLocaleString()}</span>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-p-200 text-xs">입금하실 분 성함 *</label>
            <input className={inputCls} placeholder="실제 입금자명과 같아야 자동 확인돼요"
              value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-p-200 text-xs">PDF 해설집 받으실 이메일 *</label>
            <input className={inputCls} placeholder="예: abc@email.com"
              value={form.contact} onChange={e => setForm({ ...form, contact: e.target.value })} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-p-200 text-xs">궁금한 점 (선택)</label>
            <textarea className={inputCls + ' min-h-[112px] leading-relaxed'} rows={4} style={{ resize: 'none' }}
              placeholder="예: 올해 이직 시기가 궁금해요"
              value={form.question} onChange={e => setForm({ ...form, question: e.target.value })} />
          </div>
          {error && <p className="text-[#e05070] text-xs">{error}</p>}
          <div className="flex gap-2">
            <button onClick={() => setStep('select')}
              className="flex-1 border border-p-600 text-p-200 rounded-lg py-2.5 text-sm hover:border-p-400">← 상품 변경</button>
            <button onClick={createOrder} disabled={loading}
              className="flex-[2] bg-p-400 border border-p-300 text-white font-bold rounded-lg py-2.5 text-sm hover:bg-p-350 disabled:opacity-40">
              {loading ? '주문 생성 중…' : '입금 계좌 안내받기 →'}
            </button>
          </div>
        </div>
      )}

      {step === 'deposit' && order && (
        <div className="bg-app-card border border-gold rounded-xl p-5 flex flex-col gap-4">
          <div className="text-center">
            <div className="text-p-10 font-bold mb-1">{order.product_name}</div>
            <div className="text-gold text-2xl font-bold">₩{order.amount.toLocaleString()}</div>
          </div>
          <div className="bg-app-deep border border-p-700 rounded-lg p-4 flex flex-col gap-2.5 text-sm">
            <div className="flex justify-between"><span className="text-p-200">은행</span><span className="text-p-10 font-bold">{order.bank}</span></div>
            <div className="flex justify-between items-center gap-2">
              <span className="text-p-200">계좌번호</span>
              <span className="text-p-10 font-bold select-all">{order.account}</span>
            </div>
            <div className="flex justify-between"><span className="text-p-200">예금주</span><span className="text-p-10 font-bold">{order.holder}</span></div>
            <div className="flex justify-between border-t border-p-700 pt-2.5">
              <span className="text-p-200">입금자명 ⚠️</span>
              <span className="text-gold font-bold select-all">{order.deposit_name}</span>
            </div>
          </div>
          <p className="text-p-200 text-xs leading-relaxed">
            ⚠️ 입금자명을 반드시 <span className="text-gold font-bold">{order.deposit_name}</span> 으로 입력해주세요.
            이름 뒤 숫자가 주문 확인 코드예요. 금액과 입금자명이 일치해야 자동으로 확인됩니다.
          </p>
          {status === 'deposit_claimed' ? (
            <div className="text-center py-2">
              <div className="text-gold text-sm font-bold animate-pulse">⏳ 입금 확인 중입니다…</div>
              <p className="text-p-200 text-xs mt-1.5">보통 1~2분 내 자동 확인돼요. 이 화면을 닫아도 처리됩니다.</p>
            </div>
          ) : (
            <button onClick={claimDeposit} disabled={loading}
              className="bg-p-400 border border-p-300 text-white font-bold rounded-lg py-3 text-sm hover:bg-p-350 disabled:opacity-40">
              {loading ? '확인 요청 중…' : '💸 입금 완료했어요'}
            </button>
          )}
          {error && <p className="text-[#e05070] text-xs text-center">{error}</p>}
          <button onClick={resetAll} className="text-p-200 text-xs underline">주문 취소하고 처음으로</button>
        </div>
      )}

      {step === 'done' && (
        <div className="bg-app-card border border-gold rounded-xl p-8 text-center flex flex-col gap-3">
          <div className="text-4xl">🎉</div>
          <div className="text-gold font-bold text-lg">입금이 확인됐어요!</div>
          <p className="text-p-100 text-sm leading-relaxed">
            남겨주신 이메일로 <b>24시간 내</b> PDF 해설집을 보내드릴게요.<br />
            소중한 신뢰에 정성으로 보답하겠습니다 🙏
          </p>
          <button onClick={resetAll} className="text-p-200 text-xs underline mt-2">처음으로</button>
        </div>
      )}
    </div>
  )
}
