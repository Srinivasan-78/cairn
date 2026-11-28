import { defineConfig } from 'vite'
import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import adonisjs from '@adonisjs/vite/client'
import tailwindcss from '@tailwindcss/vite'


export default defineConfig({
  plugins: [react(), tailwindcss(), adonisjs({ entryPoints: ['inertia/app/app.tsx'], reload: ['resources/views/**/*.edge'] })],

  /**
   * Define aliases for importing modules from
   * your frontend code
   */
  resolve: {
    alias: {
      '~/': `${dirname(fileURLToPath(import.meta.url))}/inertia/`,
    },
  },
  server: {
    ...(process.env.VITE_ALLOWED_HOSTS === 'true' ? { allowedHosts: true } : {}),
  }
})
