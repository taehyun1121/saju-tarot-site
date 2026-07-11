import { useEffect, useRef, useState } from 'react'
import { API } from '../api'

const PRODUCTS = [
  { key: 'single',  name: '집중 심층 리포트',  price: 25000, desc: '궁금한 주제 1개를 뿌리까지 — 시기 분석 + 3~6개월 행동 지침', emoji: '🔮' },
  { key: 'package', name: '3영역 종합 리포트', price: 35000, desc: '연애 · 재물 · 직업 심층 + 타로 연계 해석', emoji: '✨', best: true },
  { key: 'premium', name: 'VIP 풀 리포트',    price: 55000, desc: '전 영역 심층 + 10년 대운 로드맵 · 소장용 고급판', emoji: '📜' },
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

  const refreshStatus = async (orderId) => {
    try {
      const res = await fetch(`${API}/orders/${orderId}`)
      if (!res.ok) return
      const data = await res.json()
      setStatus(data.status)
      if (data.status === 'paid') {
        clearInterval(pollRef.current)
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
      <div className="text-center">
        <h2 className="text-gold text-xl font-bold mb-1">💎 심층 리포트</h2>
        <p className="text-p-200 text-sm">무료 풀이에서 못 다룬 시기 · 구체 조언까지 — 전 단계 <b className="text-gold">PDF 해설집</b>으로 보내드립니다</p>
      </div>

      {step === 'select' && (
        <div className="flex flex-col gap-3">
          {PRODUCTS.map(p => (
            <button key={p.key} onClick={() => { setProduct(p); setStep('form') }}
              className={`relative text-left bg-app-card border rounded-xl p-5 transition-all hover:border-p-300
                ${p.best ? 'border-gold' : 'border-p-600'}`}>
              {p.best && (
                <span className="absolute -top-2.5 right-4 bg-gold text-[#1a1030] text-xs font-bold px-2.5 py-0.5 rounded-full">
                  ⭐ BEST
                </span>
              )}
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-p-10 font-bold">{p.emoji} {p.name}</div>
                  <div className="text-p-200 text-xs mt-1">{p.desc}</div>
                </div>
                <div className="text-gold font-bold text-lg whitespace-nowrap">₩{p.price.toLocaleString()}</div>
              </div>
            </button>
          ))}
          <p className="text-p-200 text-xs text-center mt-1">
            결제는 무통장입금으로 진행되며, 입금 확인 후 24시간 내
            <b className="text-gold"> PDF 해설집</b>을 이메일로 보내드려요
          </p>
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
            <textarea className={inputCls} rows={3} style={{ resize: 'none' }}
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
