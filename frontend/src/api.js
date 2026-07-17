// 백엔드: Render 무료 배포(gosamtarot-backend). Railway 체험 만료로 이전(2026-07).
// 기존 VITE_API_URL 시크릿이 죽은 Railway URL이라 Render 주소로 고정.
export const API_BASE = import.meta.env.VITE_API_URL_OVERRIDE || 'https://gosamtarot-backend.onrender.com';
export const API = `${API_BASE}/api`;
