import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve('src'),
    },
  },
  server: {
    // If local TLS certs exist, serve over HTTPS so Auth0 works on non-localhost origins
    https: (() => {
      const keyPath = path.resolve('.cert/key.pem')
      const certPath = path.resolve('.cert/cert.pem')
      if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
        return {
          key: fs.readFileSync(keyPath),
          cert: fs.readFileSync(certPath),
        }
      }
      return undefined
    })(),
    // Bind to all interfaces for LAN access
    host: true, // equivalent to '0.0.0.0'
    // Use a fixed port so URLs are predictable
    port: 3003,
    // Do not fallback to a different port; fail if busy
    strictPort: true,
    // Don't auto-open to avoid popping a browser on remote hosts
    open: false,
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