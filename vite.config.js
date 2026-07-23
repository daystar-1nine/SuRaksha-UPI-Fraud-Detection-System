import { resolve } from 'path';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: './',
  plugins: [
    tailwindcss(),
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        about: resolve(__dirname, 'about.html'),
        scan: resolve(__dirname, 'scan.html'),
        profile: resolve(__dirname, 'profile.html'),
        result: resolve(__dirname, 'result.html'),
        test: resolve(__dirname, 'test.html'),
      }
    }
  }
});
