import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { VitePWA } from "vite-plugin-pwa"
import path from 'path'

// '@vueuse/core'

// injectManifest: {

// },

export default defineConfig(({ command, mode }) => {
  return {
    clearScreen: false,
    envPrefix: 'V3_',
    build: {
      sourcemap: true,
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    plugins: [
      vue(), 
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'robots.txt'],  
        strategies: 'injectManifest',
        srcDir: 'app',
        filename: 'sw.ts',
        manifest: {
          name: "V3 Project",
          short_name: "V3",
          theme_color: "#ffffff",
          start_url: "/",
          lang: "pt-BR",
          display: "standalone",
          background_color: "#ffffff",
          icons: [
            {
              "src": "/img/icons/pwa-192x192.png",
              "sizes": "192x192",
              "type": "image/png"
            },
            {
              "src": "/img/icons/pwa-512x512.png",
              "sizes": "512x512",
              "type": "image/png"
            },
            {
              "src": "/img/icons/apple-touch-icon-60x60.png",
              "sizes": "60x60",
              "type": "image/png"
            },
            {
              "src": "/img/icons/apple-touch-icon-76x76.png",
              "sizes": "76x76",
              "type": "png"
            },
            {
              "src": "/img/icons/apple-touch-icon-120x120.png",
              "sizes": "120x120",
              "type": "image/png"
            },
            {
              "src": "/img/icons/apple-touch-icon-152x152.png",
              "sizes": "152x152",
              "type": "image/png"
            },
            {
              "src": "/img/icons/apple-touch-icon-180x180.png",
              "sizes": "180x180",
              "type": "image/png"
            },
            {
              "src": "/img/icons/apple-touch-icon.png",
              "sizes": "180x180",
              "type": "image/png"
            },
            {
              "src": "/img/icons/favicon-16x16.png",
              "sizes": "16x16",
              "type": "image/png"
            },
            {
              "src": "/img/icons/favicon-32x32.png",
              "sizes": "32x32",
              "type": "image/png"
            },
            {
              "src": "/img/icons/msapplication-icon-144x144.png",
              "sizes": "144x144",
              "type": "image/png"
            },
            {
              "src": "/img/icons/mstile-150x150.png",
              "sizes": "150x150",
              "type": "image/png"
            }
          ]
        }
      })
    ]
  }
})