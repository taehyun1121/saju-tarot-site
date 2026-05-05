import { useState } from 'react'
import SajuPage from './pages/SajuPage'
import TarotPage from './pages/TarotPage'
import './App.css'

export default function App() {
  const [tab, setTab] = useState('saju')
  const [sajuData, setSajuData] = useState(null)

  return (
    <div className="app">
      <header className="header">
        <h1 className="logo">✦ 사주풀이 & 타로 ✦</h1>
        <nav className="tabs">
          <button
            className={`tab-btn ${tab === 'saju' ? 'active' : ''}`}
            onClick={() => setTab('saju')}
          >
            🔮 사주풀이
          </button>
          <button
            className={`tab-btn ${tab === 'tarot' ? 'active' : ''}`}
            onClick={() => setTab('tarot')}
          >
            🃏 타로카드
          </button>
        </nav>
      </header>

      <main className="main">
        {tab === 'saju' && (
          <SajuPage
            onGoToTarot={(data) => { setSajuData(data); setTab('tarot') }}
          />
        )}
        {tab === 'tarot' && (
          <TarotPage sajuContext={sajuData} />
        )}
      </main>
    </div>
  )
}
