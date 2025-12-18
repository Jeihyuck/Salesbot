// Plugins
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import Fonts from 'unplugin-fonts/vite'
import Layouts from 'vite-plugin-vue-layouts'
import Vue from '@vitejs/plugin-vue'
import VueRouter from 'unplugin-vue-router/vite'
import Vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

// Utilities
import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/[name].[hash].js'
      }
    }
  },
  plugins: [
    VueRouter(),
    Layouts(),
    Vue({
      template: { transformAssetUrls }
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
    Vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
    Components(),
    Fonts({
      google: {
        families: [{
          name: 'Roboto',
          styles: 'wght@100;300;400;500;700;900',
        }],
      },
    }),
    AutoImport({
      imports: [
        'vue',
        'vue-router',
      ],
      eslintrc: {
        enabled: true,
      },
      vueTemplate: true,
    }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: {
    port: 8080,
    cors: true,        // Enable CORS
    proxy: {
      // '/api': {
      //   target: 'http://localhost:8000',  // Proxy API requests to Django (running on port 8000)
      //   changeOrigin: true,
      //   rewrite: (path) => path.replace(/^\/api/, ''),
      // },
      '^/rvpr/[a-z0-9]*/api': {
        target: process.env.VITE_API_SERVER_URL,
        secure: false,
        ws: true,
        changeOrigin: true,
        // configure: (proxy) => {
        //   proxy.on('proxyReq', (proxyReq) => {
        //     // Remove 'expect' header if present
        //     proxyReq.removeHeader('expect')
        //   })
        //   proxy.on('proxyRes', (proxyRes) => {
        //     // Disable compression for SSE
        //     delete proxyRes.headers['content-encoding']
        //     delete proxyRes.headers['transfer-encoding']
        //   })
        // },
      },
      '^/rvpr/[a-z0-9]*/html': {
        target: process.env.VITE_API_SERVER_URL,
        secure: false, 
        ws: true,
        changeOrigin: true
      },
      '^/rvpr/[a-z0-9]*/static': {
        target: process.env.VITE_API_SERVER_URL,
        secure: false, 
        ws: true,
        changeOrigin: true
      },
      '^/api': {
        target: process.env.VITE_API_SERVER_URL,
        secure: false, 
        ws: true,
        changeOrigin: true,
        // configure: (proxy) => {
        //   proxy.on('proxyReq', (proxyReq) => {
        //     // Remove 'expect' header if present
        //     proxyReq.removeHeader('expect')
        //   })
        //   proxy.on('proxyRes', (proxyRes) => {
        //     // Disable compression for SSE
        //     delete proxyRes.headers['content-encoding']
        //     delete proxyRes.headers['transfer-encoding']
        //   })
        // },
      },
      '^/html': {
        target: process.env.VITE_API_SERVER_URL,
        secure: false, 
        ws: true,
        changeOrigin: true
      },
      '^/static': {
        target: process.env.VITE_API_SERVER_URL,
        secure: false, 
        ws: true,
        changeOrigin: true
      }
    },
    compress: false
  },
})
