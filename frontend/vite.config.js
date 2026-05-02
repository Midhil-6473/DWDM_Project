import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiProxy = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8005";

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5200,
      strictPort: true,
      proxy: {
        "/meta": { target: apiProxy, changeOrigin: true },
        "/predict": { target: apiProxy, changeOrigin: true },
        "/analytics": { target: apiProxy, changeOrigin: true },
        "/health": { target: apiProxy, changeOrigin: true }
      }
    }
  };
});
