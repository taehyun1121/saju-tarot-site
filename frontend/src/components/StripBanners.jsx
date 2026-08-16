// 🔴 2026-08-16 — 크몽 전환 퍼널 반영(소셜봇 설계, blog/kmong_funnel_design.md).
// 저가(734044) 먼저 → 고가(778578) BEST. 무속 프레이밍 배제, "계산·정통성" 이중신뢰층 문구.
const KMONG_GIGS = [
  {
    url: 'https://kmong.com/gig/734044',
    icon: '🌿',
    tier: '가볍게 궁금한 것부터',
    text: '크몽 가벼운 상담',
    best: false,
  },
  {
    url: 'https://kmong.com/gig/778578',
    icon: '🔮',
    tier: '진지하게 풀어야 할 고민',
    text: '크몽 심층 상담',
    best: true,
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

// 사이트 상시 스트립(랜딩 어디서든) — 헤드라인 한 줄, 저가 gig로 연결(낮은 장벽 진입점).
export function KmongStripBanners() {
  return (
    <a
      href={KMONG_GIGS[0].url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-center gap-2 w-full
                 bg-gradient-to-r from-p-900 via-rose-accent/40 to-p-900
                 border-b border-p-700 py-2 px-3
                 text-p-10 text-sm max-sm:text-xs text-center
                 hover:bg-p-800 hover:text-gold transition-all"
    >
      <span className="font-bold">
        감이 아니라 계산으로 짚어드립니다 — 더 깊은 리딩은 신내림 마스터 개인상담으로
      </span>
      <span className="text-gold whitespace-nowrap font-bold
                       bg-p-700 border border-p-500 rounded-full
                       px-3 py-0.5 text-xs max-sm:px-2 shrink-0">
        크몽 상담 →
      </span>
    </a>
  )
}

// AI 상담결과 화면 전용 — 값을 받은 직후(전환 골든타임), 저가→고가 2단 CTA.
export function KmongResultCTA() {
  return (
    <div className="w-full py-4 px-3 border-t border-p-700">
      <p className="text-center text-sm max-sm:text-xs text-p-50 font-bold mb-3">
        방금 계산으로 흐름을 봤다면, 이제 사람이 직접 — 신내림 마스터가 검증한 리딩
      </p>
      <div className="flex flex-col sm:flex-row gap-2">
        {KMONG_GIGS.map(gig => (
          <a
            key={gig.url}
            href={gig.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`relative flex-1 flex flex-col items-center gap-1 rounded-lg
                       border py-3 px-3 text-center transition-all
                       ${gig.best
                         ? 'bg-gradient-to-b from-gold/20 to-p-900 border-gold hover:brightness-110'
                         : 'bg-p-900 border-p-700 hover:bg-p-800'}`}
          >
            {gig.best && (
              <span className="absolute -top-2 right-2 bg-gold text-p-900 text-[10px]
                               font-bold px-2 py-0.5 rounded-full">
                BEST
              </span>
            )}
            <span className="text-xl">{gig.icon}</span>
            <span className="text-xs max-sm:text-[11px] text-p-100">{gig.tier}</span>
            <span className="font-bold text-sm max-sm:text-xs text-gold">{gig.text}</span>
            {gig.best && (
              <span className="text-[11px] text-p-100">가벼운 상담 + 사주·타로 교차 심층분석</span>
            )}
            <span className="mt-1 text-xs max-sm:text-[11px] font-bold text-p-10
                             bg-p-700 border border-p-500 rounded-full px-3 py-0.5">
              지금 이 고민 풀기 →
            </span>
          </a>
        ))}
      </div>
    </div>
  )
}
