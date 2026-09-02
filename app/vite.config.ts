import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    // `make dev` runs Vite alongside Uvicorn; the built app is served by Uvicorn itself.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
});
