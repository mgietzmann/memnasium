import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

/** One local page. `make dev` proxies /api to the Uvicorn process. */
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
