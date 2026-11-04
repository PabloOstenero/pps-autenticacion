/* Avisos (toasts) globales muy simples. */
import { reactive } from "vue";

export const avisos = reactive([]);

export function aviso(mensaje, tipo = "info") {
  const id = `${Date.now()}-${Math.random()}`;
  avisos.push({ id, mensaje, tipo });
  setTimeout(() => {
    const i = avisos.findIndex((a) => a.id === id);
    if (i !== -1) avisos.splice(i, 1);
  }, 4000);
}
