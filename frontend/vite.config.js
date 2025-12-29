import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'onnx-mime-type',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url?.endsWith('.onnx')) {
            res.setHeader('Content-Type', 'application/octet-stream')
          }
          next()
        })
      }
    }
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/hmt': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/cognitive': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/tracking': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/audit': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/experience': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/integrated': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/brain': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    },
    host: true
  },
  optimizeDeps: {
    exclude: ['onnxruntime-web']
  },
  assetsInclude: ['**/*.onnx']
})
