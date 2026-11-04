import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/favicon.svg', 'icons/apple-touch-icon.png'],
      manifest: {
        name: 'BT COMPTA PRO',
        short_name: 'BT Compta',
        description: 'Formation BT1/BT2, calculatrices comptables et comptabilité SYSCOHADA — Mali',
        lang: 'fr',
        id: '/app',
        start_url: '/app',
        scope: '/',
        display: 'standalone',
        display_override: ['standalone'],
        dir: 'ltr',
        orientation: 'any',
        background_color: '#F3F5F8',
        theme_color: '#102B55',
        categories: ['education', 'finance', 'productivity'],
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
        // Appui long sur l'icône de l'application (Android, Windows)
        shortcuts: [
          { name: 'Calculatrices', short_name: 'Calculs', url: '/app/calculatrices', icons: [{ src: '/icons/shortcut-calc.png', sizes: '96x96', type: 'image/png' }] },
          { name: 'Mes cours', short_name: 'Cours', url: '/app/formation/BT1', icons: [{ src: '/icons/shortcut-cours.png', sizes: '96x96', type: 'image/png' }] },
          { name: 'Quiz et examens', short_name: 'Examens', url: '/app/examens', icons: [{ src: '/icons/shortcut-examens.png', sizes: '96x96', type: 'image/png' }] },
          { name: 'Gestion comptable', short_name: 'Compta', url: '/app/comptabilite', icons: [{ src: '/icons/shortcut-compta.png', sizes: '96x96', type: 'image/png' }] },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//, /^\/admin\//],
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        globIgnores: ['splash/**'],
        runtimeCaching: [
          {
            // Catalogue pédagogique et calculatrices consultables hors connexion
            urlPattern: ({ url }) => url.pathname.startsWith('/api/pedagogy/') || url.pathname === '/api/calculations/',
            handler: 'NetworkFirst',
            options: { cacheName: 'api-catalogue', networkTimeoutSeconds: 4, expiration: { maxEntries: 100, maxAgeSeconds: 7 * 24 * 3600 } },
          },
        ],
      },
      devOptions: { enabled: false },
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/admin': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  preview: {
    port: 4173,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  },
});
