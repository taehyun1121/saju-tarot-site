import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    host: true,
    allowedHosts: true,
    proxy: { '/api': 'http://localhost:8001', '/static': 'http://localhost:8001' }
  }
})
