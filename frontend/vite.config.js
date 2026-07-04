import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  // 커스텀 도메인(gosamtarot.com) 전환 시 CUSTOM_DOMAIN=1로 빌드 → base '/'
  base: process.env.CUSTOM_DOMAIN === '1' ? '/' : '/saju-tarot-site/',
  plugins: [tailwindcss(), react()],
  define: {
    __API_BASE__: JSON.stringify(process.env.VITE_API_URL || ''),
  },
  server: {
    host: true,
    allowedHosts: true,
    proxy: { '/api': 'http://localhost:8001', '/static': 'http://localhost:8001' }
  }
})
