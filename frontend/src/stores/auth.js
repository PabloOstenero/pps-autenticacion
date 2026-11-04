import { defineStore } from "pinia";
import { solicitar } from "../api";
import { guardarTokens, limpiarTokens, obtenerRefresh } from "../tokens";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    usuario: null, // { username, rol, creado }
    listo: false,  // el arranque (lectura de sesión) ya terminó
  }),

  getters: {
    autenticado: (s) => !!s.usuario,
    rol: (s) => s.usuario?.rol ?? null,
    esGestor: (s) => s.usuario?.rol === "owner" || s.usuario?.rol === "staff",
    esDueno: (s) => s.usuario?.rol === "owner",
  },

  actions: {
    /** Al arrancar: si hay refresh token guardado, recupera la sesión. */
    async iniciar() {
      if (obtenerRefresh()) {
        try {
          this.usuario = await solicitar("/auth/me");
        } catch {
          limpiarTokens();
          this.usuario = null;
        }
      }
      this.listo = true;
    },

    async iniciarSesion(credenciales) {
      const r = await solicitar("/auth/login", { metodo: "POST", cuerpo: credenciales, auth: false });
      guardarTokens(r.access_token, r.refresh_token);
      this.usuario = r.usuario;
      return r.usuario;
    },

    async registrar(datos) {
      const r = await solicitar("/auth/registro", { metodo: "POST", cuerpo: datos, auth: false });
      guardarTokens(r.access_token, r.refresh_token);
      this.usuario = r.usuario;
      return r.usuario;
    },

    async cerrarSesion() {
      const refresh_token = obtenerRefresh();
      try {
        await solicitar("/auth/logout", { metodo: "POST", cuerpo: { refresh_token } });
      } catch {
        /* aunque falle, cerramos en local */
      }
      limpiarTokens();
      this.usuario = null;
    },
  },
});
