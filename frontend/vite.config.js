import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'

function loadProxy() {
  const configPath = path.resolve(__dirname, '../../../sites/common_site_config.json')
  if (!fs.existsSync(configPath)) {
    return {}
  }
  try {
    const { getProxyOptions } = require('frappe-ui/src/utils/vite-dev-server')
    const { webserver_port } = JSON.parse(fs.readFileSync(configPath, 'utf8'))
    return getProxyOptions({ port: webserver_port })
  } catch (e) {
    return {}
  }
}

export default defineConfig(({ command }) => ({
  plugins: [vue()],
  base: command === 'build' ? '/assets/insurance_core/frontend/' : '/',
  server: {
    host: true,
    port: 8080,
    allowedHosts: ['.monkeycode-ai.live'],
    proxy: loadProxy(),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../insurance_core/public/frontend',
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name].[ext]',
      },
    },
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client'],
  },
}))
