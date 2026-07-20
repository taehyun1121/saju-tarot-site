import { useState, useEffect, useRef } from 'react'
import { API } from '../api'

// 무통장입금 주문 모달 — 백엔드 orders.py(계좌매칭+RTPay웹훅+bankapi 자동승인)를 처음으로 프론트에 연결.
// 디자인: 디자인봇 gate:payment_modal 목업(payment_modal.html/_mobile.html) 그대로 이식(.paymodal 스코프).
// 흐름: 입금자명/연락처 입력 → 주문생성(POST /api/orders) → 계좌정보+매칭코드 안내(입금자명 최상위 강조) →
//   "입금했어요" 클릭(POST /api/orders/{id}/claim) → 대기 중이면 5초 간격 폴링(GET /api/orders/{id})으로 자동승인 반영.
export default function OrderModal({ open, onClose, productKey, amount, productName, defaultName = '' }) {
  const [step, setStep] = useState('form') // form | account | polling | paid
  const [name, setName] = useState(defaultName)
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [order, setOrder] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState('') // 'name' | 'account' | ''
  const pollRef = useRef(null)
  const copyTimerRef = useRef(null)

  useEffect(() => {
    if (open) { setStep('form'); setName(defaultName); setPhone(''); setEmail(''); setOrder(null); setError('') }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current)
    }
  }, [open, defaultName])

  if (!open) return null

  const submitOrder = async () => {
    if (!name.trim()) { setError('입금자명을 입력해 주세요'); return }
    if (!phone.trim()) { setError('휴대폰번호를 입력해 주세요'); return }
    if (!email.trim()) { setError('이메일을 입력해 주세요'); return }
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API}/orders`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product: productKey, buyer_name: name.trim(),
          contact: `${phone.trim()} / ${email.trim()}`,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '주문 생성에 실패했습니다')
      setOrder(data)
      setStep('account')
    } catch (e) {
      setError(e.message === 'Failed to fetch' ? '서버에 연결할 수 없습니다' : e.message)
    } finally { setLoading(false) }
  }

  const claimDeposit = async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API}/orders/${order.order_id}/claim`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '확인 요청에 실패했습니다')
      if (data.status === 'paid') { setStep('paid'); return }
      setStep('polling')
      pollRef.current = setInterval(async () => {
        try {
          const r = await fetch(`${API}/orders/${order.order_id}`)
          const d = await r.json()
          if (d.status === 'paid') {
            clearInterval(pollRef.current)
            setStep('paid')
          }
        } catch { /* 다음 폴링에서 재시도 */ }
      }, 5000)
    } catch (e) {
      setError(e.message === 'Failed to fetch' ? '서버에 연결할 수 없습니다' : e.message)
    } finally { setLoading(false) }
  }

  const copy = (text, key) => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(key)
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current)
      copyTimerRef.current = setTimeout(() => setCopied(''), 1500)
    }).catch(() => {})
  }

  return (
    <div className="paymodal-backdrop" onClick={onClose}>
      <div className="paymodal" onClick={e => e.stopPropagation()}>
        <div className="paymodal-dan" />

        {step === 'form' && (
          <>
            <div className="paymodal-head">
              <button className="paymodal-x" onClick={onClose} aria-label="닫기">✕</button>
              <div className="t serif">무통장 <b>입금</b> 안내</div>
              <div className="s">아래 정보를 입력하시면 계좌를 안내드립니다</div>
            </div>
            <div className="paymodal-body">
              <div className="paymodal-summary"><div className="nm">{productName}</div><div className="pr serif">{amount.toLocaleString()}원</div></div>
              <div className="paymodal-field"><label>입금자명</label>
                <input value={name} onChange={e => setName(e.target.value)} placeholder="예) 김지현" maxLength={20} />
              </div>
              <div className="paymodal-field"><label>휴대폰번호</label>
                <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="010-0000-0000" inputMode="tel" />
              </div>
              <div className="paymodal-field"><label>이메일</label>
                <input value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com" inputMode="email" />
              </div>
              {error && <div className="paymodal-error">{error}</div>}
              <button className="paymodal-cta" disabled={loading} onClick={submitOrder}>
                {loading ? '계좌 안내 준비 중…' : '계좌 안내받기'}
              </button>
            </div>
          </>
        )}

        {(step === 'account' || step === 'polling') && order && (
          <>
            <div className="paymodal-head">
              <button className="paymodal-x" onClick={onClose} aria-label="닫기">✕</button>
              <div className="t serif">아래 계좌로 <b>입금</b>해 주세요</div>
              <div className="s">입금자명이 다르면 자동확인이 안 됩니다</div>
            </div>
            <div className="paymodal-body">
              <div className="paymodal-namebox">
                <div className="lbl">⚠️ 입금자명 — 반드시 이 이름 그대로</div>
                <div className="val">
                  <span className="nm serif">{order.deposit_name}</span>
                  <span className={`paymodal-copy${copied === 'name' ? ' copied' : ''}`} onClick={() => copy(order.deposit_name, 'name')}>{copied === 'name' ? '복사됨' : '복사'}</span>
                </div>
                <div className="warn">뒤 코드까지 붙여서 입금해야 자동 매칭됩니다. 이름만 입금 시 확인 지연.</div>
              </div>
              <div className="paymodal-acc">
                <div className="paymodal-row hot"><span className="k">계좌번호</span>
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <span className="v">{order.account}</span>
                    <span className={`paymodal-copy${copied === 'account' ? ' copied' : ''}`} onClick={() => copy(order.account, 'account')}>{copied === 'account' ? '복사됨' : '복사'}</span>
                  </span>
                </div>
                <div className="paymodal-row"><span className="k">은행</span><span className="v">{order.bank}</span></div>
                <div className="paymodal-row"><span className="k">예금주</span><span className="v">{order.holder}</span></div>
                <div className="paymodal-row"><span className="k">입금액</span><span className="v" style={{ color: 'var(--gold)' }}>{order.amount.toLocaleString()}원</span></div>
              </div>
              <div className="paymodal-notice">· 24시간 자동입금 확인 시스템으로 운영됩니다.<br />· 입금 후 아래 버튼을 눌러주시면 확인이 빨라집니다.</div>
              {error && <div className="paymodal-error">{error}</div>}
              {step === 'polling' ? (
                <div className="paymodal-wait">
                  <div className="paymodal-spin" />
                  <div className="wt serif">입금을 확인하고 있습니다…</div>
                  <div className="ws">보통 <b style={{ color: 'var(--gold)' }}>1~2분</b> 내에 자동으로 확인됩니다.<br />이 창을 닫으셔도 확인은 계속 진행됩니다.</div>
                  <div className="paymodal-dots"><i /><i /><i /></div>
                </div>
              ) : (
                <>
                  <button className="paymodal-cta" disabled={loading} onClick={claimDeposit}>
                    {loading ? '확인 중…' : '입금했어요'}
                  </button>
                  <button className="paymodal-cta ghost" onClick={() => setStep('form')}>입금정보 다시 입력</button>
                </>
              )}
            </div>
          </>
        )}

        {step === 'paid' && (
          <>
            <div className="paymodal-head">
              <button className="paymodal-x" onClick={onClose} aria-label="닫기">✕</button>
              <div className="t serif"><b>입금 확인</b> 완료</div>
            </div>
            <div className="paymodal-body">
              <div className="paymodal-done">
                <div className="paymodal-check">✓</div>
                <div className="dt serif">입금이 확인되었습니다</div>
                <div className="ds">신청하신 리딩은 <b>24시간 이내</b><br />입력하신 연락처로 전달됩니다.<br />잠시만 기다려 주세요 🙏</div>
                <button className="paymodal-cta" style={{ marginTop: 22 }} onClick={onClose}>확인</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
