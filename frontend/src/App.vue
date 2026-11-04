<script setup>
import { onMounted, watch } from "vue";
import { useAuthStore } from "./stores/auth";
import { useCarritoStore } from "./stores/carrito";
import { avisos } from "./avisos";
import AppHeader from "./components/AppHeader.vue";

const auth = useAuthStore();
const carrito = useCarritoStore();

// El contador del carrito (menú) se mantiene al día tras iniciar sesión.
onMounted(() => {
  if (auth.autenticado) carrito.cargar();
});
watch(
  () => auth.autenticado,
  (dentro) => {
    if (dentro) carrito.cargar();
    else carrito.limpiar();
  }
);
</script>

<template>
  <div class="fondo" aria-hidden="true">
    <span class="blob b1"></span>
    <span class="blob b2"></span>
    <span class="blob b3"></span>
    <div class="rejilla"></div>
    <div class="scanlines"></div>
  </div>

  <AppHeader v-if="auth.autenticado" />

  <main class="contenido">
    <RouterView />
  </main>

  <div class="avisos" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="a in avisos" :key="a.id" :class="['toast', a.tipo]">{{ a.mensaje }}</div>
    </TransitionGroup>
  </div>
</template>
