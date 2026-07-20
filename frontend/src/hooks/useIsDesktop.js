import { useState, useEffect } from 'react'

// 900px 브레이크포인트 — funnel.css의 @media(min-width:900px)와 동일 기준.
export default function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(min-width: 900px)').matches
  )
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 900px)')
    const onChange = () => setIsDesktop(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return isDesktop
}
