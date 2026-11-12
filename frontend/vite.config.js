import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// El frontend vive en su propio servidor (5173) y consume la API por HTTP.
// La URL de la API se configura con VITE_API_URL (ver .env).
export default defineConfig({
  base: "/pps-autenticacion/",
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
