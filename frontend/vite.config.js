import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  base: '/saju-tarot-site/',
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
