import { useState, useEffect } from 'react'
import SajuPage from './pages/SajuPage'
import TarotPage from './pages/TarotPage'
import HistoryPage from './pages/HistoryPage'
import PremiumPage from './pages/PremiumPage'
import { DomainStripBanner } from './components/StripBanners'

export default function App() {
  // 초기 탭: URL ?tab=premium 또는 #premium 이면 바로 그 탭(라이트→가격 딥링크·프리뷰용). 없으면 사주.
  const [tab, setTab] = useState(() => {
    try {
      const q = new URLSearchParams(window.location.search).get('tab')
      const h = window.location.hash.replace('#', '')
      const req = q || h
      if (['saju', 'tarot', 'premium'].includes(req)) return req
    } catch { /* ignore */ }
    return 'saju'
  })
  const [sajuData, setSajuData] = useState(null)
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('saju-tarot-history')
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })

  // 시간대 자동 톤 전환: 낮(06~18)=라이트 베이지 / 밤=다크 (라이트 사이트와 통일, 토글 없음).
  // 1분마다 재확인 → 열어둔 채 경계(18:00 등) 넘으면 자동 전환.
  useEffect(() => {
    const apply = () => {
      const h = new Date().getHours()
      document.documentElement.dataset.theme = (h >= 6 && h < 18) ? 'light' : 'dark'
    }
    apply()
    const id = setInterval(apply, 60 * 1000)
    return () => clearInterval(id)
  }, [])

  const saveHistory = (entries) => {
    setHistory(prev => {
      const next = [...entries, ...prev]
      localStorage.setItem('saju-tarot-history', JSON.stringify(next))
      return next
    })
  }

  const updateHistoryTarot = (historyId, tarotResult) => {
    setHistory(prev => {
      const next = prev.map(entry =>
        entry.id === historyId
          ? { ...entry, type: 'saju+tarot', tarot: tarotResult }
          : entry
      )
      localStorage.setItem('saju-tarot-history', JSON.stringify(next))
      return next
    })
  }

  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem('saju-tarot-history')
  }

  // 🔒 히스토리 = 관리자 전용. URL에 ?admin 또는 #admin 있을 때만 탭 노출(일반 유저에겐 숨김).
  //    기능·페이지·localStorage 로직은 그대로 유지 — 버튼만 감춤.
  const isAdmin = (() => {
    try {
      return new URLSearchParams(window.location.search).has('admin') || window.location.hash === '#admin'
    } catch { return false }
  })()

  const tabs = [
    { id: 'saju',    label: '🔮 사주로 물어보기' },
    { id: 'tarot',   label: '🃏 타로로 물어보기' },
    { id: 'premium', label: '💎 심화 풀이(정밀 리포트)' },
    ...(isAdmin ? [{ id: 'history', label: `📋 히스토리(관리자)${history.length > 0 ? ` ${history.length}` : ''}` }] : []),
  ]

  return (
    <div className="min-h-screen flex flex-col">
      {/* <DomainStripBanner /> — 도메인(gosamtarot.com) 구입 전까지 임시 숨김 (2026-07-11) */}
      <header className="bg-gradient-to-br from-p-900 to-p-800 border-b border-p-500 px-6 py-4 sticky top-0 z-10
                         flex items-center gap-8
                         max-md:flex-col max-md:items-start max-md:gap-3 max-md:px-4 max-md:py-3
                         max-sm:px-3 max-sm:py-2.5 max-sm:gap-2">
        <h1 className="text-gold tracking-widest whitespace-nowrap
                       text-xl max-md:text-lg max-sm:text-base">
          ✦ 사주풀이 & 타로 ✦
        </h1>
        {/* 진입 선택 = 셀렉트 박스: 사주로 물어보기 / 타로로 물어보기 중 하나만 (라이트 사이트와 통일) */}
        <label className="flex items-center gap-2 max-md:w-full">
          <span className="text-p-200 text-sm whitespace-nowrap max-sm:hidden">무엇을 보시겠어요?</span>
          <select
            value={tab}
            onChange={(e) => setTab(e.target.value)}
            aria-label="무엇을 보시겠어요?"
            className="bg-app-input border border-p-500 text-p-10 rounded-lg h-[46px] px-4 text-sm
                       outline-none focus:border-p-300 cursor-pointer w-[240px]
                       max-md:w-full"
          >
            {tabs.map(t => (
              <option key={t.id} value={t.id} className="bg-app-card text-p-10">{t.label}</option>
            ))}
          </select>
        </label>
      </header>

      <main className="flex-1 p-6 max-w-[1200px] mx-auto w-full
                       max-lg:p-5 max-md:p-4 max-sm:p-3">
        {tab === 'saju' && (
          <SajuPage
            onGoToTarot={(data) => { setSajuData(data); setTab('tarot') }}
            onSaveHistory={saveHistory}
          />
        )}
        {tab === 'tarot' && (
          <TarotPage
            sajuContext={sajuData}
            onSaveTarot={updateHistoryTarot}
            onSaveNewTarot={(entry) => saveHistory([entry])}
          />
        )}
        {tab === 'premium' && <PremiumPage />}
        {tab === 'history' && (
          <HistoryPage history={history} onClear={clearHistory} />
        )}
      </main>

      {/* 공통 푸터 — 서비스 고지 + 시간대 테마 안내 + 카피라이트 (라이트/가격안내/프로 공통 톤) */}
      <footer className="border-t border-p-700 px-6 py-6 mt-6 flex flex-col items-center gap-2.5 text-center
                         max-sm:px-4">
        <p className="text-p-200 text-[11px] leading-relaxed max-w-[600px]">
          본 서비스는 사주·타로에 기반한 상담·참고용 콘텐츠로, 오락 및 자기이해를 돕는 목적입니다.
          의료·법률·재정 등 전문적 판단을 대체하지 않으며, 최종 결정과 책임은 본인에게 있습니다.
        </p>
        <p className="text-p-300 text-[11px]">🌗 이 사이트는 지금 시간대에 맞춰 낮·밤 테마가 자동으로 바뀌어요.</p>
        <p className="text-p-300 text-[11px]">© 2026 고삼타로(thha301) · All rights reserved.</p>
      </footer>
    </div>
  )
}
