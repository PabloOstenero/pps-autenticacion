import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import { alExpirarSesion } from "./api";
import { useAuthStore } from "./stores/auth";
import "./styles.css";

async function arrancar() {
  const app = createApp(App);
  const pinia = createPinia();
  app.use(pinia);

  const auth = useAuthStore();

  // Si la sesión caduca del todo (refresh inválido), volvemos al acceso.
  alExpirarSesion(() => {
    auth.usuario = null;
    router.replace({ name: "acceso" });
  });

  // Recuperamos la sesión ANTES de montar, para que las guardas del router
  // tengan el estado correcto en la primera navegación.
  await auth.iniciar();

  app.use(router);
  app.mount("#app");
}

arrancar();
