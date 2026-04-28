import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  // Public asset path served by Frappe — matches the URL prefix used by
  // www/booncrm.py when reading the manifest and rendering script tags.
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
    // Emit .vite/manifest.json so the booncrm.py www handler can
    // resolve content-hashed entry chunk paths at request time —
    // survives Cloudflare cache regardless of query strings.
    manifest: true,
    rollupOptions: {
      output: {
        // Content-hashed filenames for ALL chunks so cache invalidation
        // is path-based (not query-string-based, which Cloudflare strips).
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
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
