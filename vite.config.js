import { defineConfig } from 'vite';
import path from 'path';

// Plugin to add COOP/COEP headers for SharedArrayBuffer support
function crossOriginIsolation() {
  return {
    name: 'cross-origin-isolation',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
        res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
        next();
      });
    }
  };
}

export default defineConfig({
  root: 'apps/static',

  plugins: [crossOriginIsolation()],

  build: {
    outDir: path.resolve(process.cwd(), 'apps/static/dist'),
    emptyOutDir: true,

    rollupOptions: {
      input: {
        main: path.resolve(process.cwd(), 'apps/static/js/app.js')
      },

      output: {
        manualChunks: {
          'turso-wasm': ['@tursodatabase/database-wasm']
        },

        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    },

    target: 'esnext',
    minify: 'terser'
  },

  optimizeDeps: {
    exclude: ['@tursodatabase/database-wasm']
  },

  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
