import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Use relative-adjacent absolute base '/' for Vercel/Netlify.
  // If you deploy to GitHub Pages under /<repo-name>/, change to '/crop-disease-detection/'
  base: '/',
  build: {
    outDir: 'dist',
  },
  optimizeDeps: {
    // Only scan real source files — never wander into backend data/venvs.
    entries: ['index.html', 'src/main.jsx'],
    include: ['react', 'react-dom', 'react-router-dom', 'lucide-react'],
    force: false,
  },
  server: {
    port: 5173,
    strictPort: true,
    host: '127.0.0.1',
    // Auto-open the app in your default browser on `npm run dev`.
    open: '/login',
    // Don't let the file watcher crawl the huge backend folders
    // (dataset images, venvs) — that can hang the dev server on Windows.
    watch: {
      ignored: [
        '**/backend/venv/**',
        '**/backend/venv311/**',
        '**/backend/dataset/**',
        '**/backend/__pycache__/**',
        '**/dist/**',
      ],
    },
    proxy: {
      // Lets `fetch('/api/predict')` work in dev without CORS issues.
      // Backend: cd backend && uvicorn main:app --reload --port 8000
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})

