import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite' // Import

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // Add plugin
  ],
})
