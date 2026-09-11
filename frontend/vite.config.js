import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/agri_engine': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
