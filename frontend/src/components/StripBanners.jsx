const KMONG_GIGS = [
  {
    url: 'https://kmong.com/gig/778578',
    icon: '🔮',
    text: '왜 반복될까요? 사주·타로로 이유 찾아드려요',
  },
  {
    url: 'https://kmong.com/gig/734044',
    icon: '💜',
    text: '연애·재회 고민, 결과 흐름 지금 알려드려요',
  },
]

export function DomainStripBanner() {
  return (
    <a
      href="https://gosamtarot.com"
      className="block w-full bg-gradient-to-r from-p-800 via-p-600 to-p-800
                 border-b border-p-500 text-center py-1.5 px-3
                 text-gold tracking-widest font-bold
                 text-sm max-sm:text-xs max-sm:tracking-wide
                 hover:brightness-125 transition-all"
    >
      ✦ 공식 홈페이지 gosamtarot.com ✦
    </a>
  )
}

export function KmongStripBanners() {
  return (
    <div className="w-full">
      {KMONG_GIGS.map(gig => (
        <a
          key={gig.url}
          href={gig.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 w-full
                     bg-gradient-to-r from-p-900 via-rose-accent/40 to-p-900
                     border-b border-p-700 py-2 px-3
                     text-p-10 text-sm max-sm:text-xs
                     hover:bg-p-800 hover:text-gold transition-all"
        >
          <span>{gig.icon}</span>
          <span className="font-bold truncate">{gig.text}</span>
          <span className="text-gold whitespace-nowrap font-bold
                           bg-p-700 border border-p-500 rounded-full
                           px-3 py-0.5 text-xs max-sm:px-2">
            크몽 1:1 상담 →
          </span>
        </a>
      ))}
    </div>
  )
}
