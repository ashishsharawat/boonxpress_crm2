import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  // Public asset path served by Frappe — matches the URL prefix in www/booncrm.html.
  base: '/assets/boonxpress_crm/frontend/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: path.resolve(__dirname, '..', 'boonxpress_crm', 'public', 'frontend'),
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      output: {
        // Static filenames for entry chunks so the booncrm.html template can
        // reference them with a stable URL. Lazy-loaded route chunks keep
        // their content hashes for cache busting.
        entryFileNames: 'assets/index.js',
        chunkFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'vendor') return 'assets/vendor.js'
          return 'assets/[name]-[hash].js'
        },
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith('.css')) return 'assets/index.css'
          return 'assets/[name]-[hash][extname]'
        },
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
        },
      },
    },
  },
  server: {
    port: 8081,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/assets': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
