import { useState } from 'react'
import SajuPage from './pages/SajuPage'
import TarotPage from './pages/TarotPage'
import HistoryPage from './pages/HistoryPage'
import PremiumPage from './pages/PremiumPage'

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

  const tabs = [
    { id: 'saju',    label: '🔮 사주풀이' },
    { id: 'tarot',   label: '🃏 타로카드' },
    { id: 'premium', label: '💎 심화풀이' },
    { id: 'history', label: `📋 히스토리${history.length > 0 ? ` (${history.length})` : ''}` },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gradient-to-br from-p-900 to-p-800 border-b border-p-500 px-6 py-4 sticky top-0 z-10
                         flex items-center gap-8
                         max-md:flex-col max-md:items-start max-md:gap-3 max-md:px-4 max-md:py-3
                         max-sm:px-3 max-sm:py-2.5 max-sm:gap-2">
        <h1 className="text-gold tracking-widest whitespace-nowrap
                       text-xl max-md:text-lg max-sm:text-base">
          ✦ 사주풀이 & 타로 ✦
        </h1>
        <nav className="flex gap-2 max-md:w-full">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`
                border rounded-full transition-all text-sm px-5 py-2
                max-md:flex-1 max-md:rounded-lg max-md:text-center max-md:px-2 max-md:py-2
                max-sm:text-xs max-sm:py-1.5
                ${tab === t.id
                  ? 'bg-p-400 border-p-300 text-white font-bold'
                  : 'bg-transparent border-p-500 text-p-150 hover:border-p-350 hover:text-p-50'}
              `}
            >
              {t.label}
            </button>
          ))}
        </nav>
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
