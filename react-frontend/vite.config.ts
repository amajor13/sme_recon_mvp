import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve('src'),
    },
  },
  server: {
    // Prefer port 3002 to match Auth0 allowed callbacks
    port: 3003,
    // Allow alternative port if 3002 is busy
    strictPort: false,
    // Open in the system default browser (avoids VS Code Simple Browser auth issues)
    open: true,
    proxy: {
      '/api': {
        // Backend FastAPI runs on port 8004
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})