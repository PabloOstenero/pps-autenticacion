import { defineStore } from "pinia";
import { solicitar } from "../api";

export const useCarritoStore = defineStore("carrito", {
  state: () => ({
    items: [],
    total: 0,
    numArticulos: 0,
    cargado: false,
  }),

  actions: {
    aplicar(carrito) {
      this.items = carrito.items;
      this.total = carrito.total;
      this.numArticulos = carrito.num_articulos;
      this.cargado = true;
    },

    async cargar() {
      try {
        this.aplicar(await solicitar("/carrito"));
      } catch {
        /* sin sesión: lo gestiona el router */
      }
    },

    async anadir(videojuegoId, cantidad = 1) {
      this.aplicar(await solicitar(`/carrito?videojuego_id=${videojuegoId}&cantidad=${cantidad}`, { metodo: "POST" }));
    },

    async cambiarCantidad(videojuegoId, cantidad) {
      this.aplicar(await solicitar(`/carrito/${videojuegoId}?cantidad=${cantidad}`, { metodo: "PATCH" }));
    },

    async quitar(videojuegoId) {
      this.aplicar(await solicitar(`/carrito/${videojuegoId}`, { metodo: "DELETE" }));
    },

    async vaciar() {
      this.aplicar(await solicitar("/carrito", { metodo: "DELETE" }));
    },

    limpiar() {
      this.items = [];
      this.total = 0;
      this.numArticulos = 0;
      this.cargado = false;
    },
  },
});
