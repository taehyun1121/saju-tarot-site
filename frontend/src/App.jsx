import { useState } from 'react'
import SajuPage from './pages/SajuPage'
import TarotPage from './pages/TarotPage'
import HistoryPage from './pages/HistoryPage'
import PremiumPage from './pages/PremiumPage'
import { DomainStripBanner } from './components/StripBanners'

export default function App() {
  const [tab, setTab] = useState('saju')
  const [sajuData, setSajuData] = useState(null)
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('saju-tarot-history')
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })

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
    </div>
  )
}
