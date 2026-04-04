// Iron Arena — Vite Configuration
// Created by: engineering-frontend-developer
// Purpose: Vite build config for React+TypeScript Telegram Mini App

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: [
      "all",
      ".ngrok-free.dev",
      "superseriously-vixenly-leisa.ngrok-free.dev",
    ],
    proxy: {
      "/api": {
        target: "https://iron-arena.onrender.com",
        changeOrigin: true,
      },
      "/ws": {
        target: "wss://iron-arena.onrender.com",
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
