// 프로덕션: VITE_API_URL 환경변수 사용, 개발: 로컬 프록시 사용
export const API_BASE = import.meta.env.VITE_API_URL || '';
export const API = `${API_BASE}/api`;
