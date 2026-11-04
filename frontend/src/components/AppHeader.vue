<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useCarritoStore } from "../stores/carrito";
import { aviso } from "../avisos";

const auth = useAuthStore();
const carrito = useCarritoStore();
const router = useRouter();
const route = useRoute();

const abierto = ref(false);

const enlaces = computed(() => {
  const base = [
    { ruta: "tienda", texto: "Tienda" },
    { ruta: "carrito", texto: "Carrito", badge: carrito.numArticulos },
    { ruta: "pedidos", texto: "Mis pedidos" },
  ];
  if (auth.esGestor) {
    base.push({ ruta: "publicar", texto: "Publicar juego" });
    base.push({ ruta: "pedidos-tienda", texto: "Pedidos de la tienda" });
  }
  if (auth.esDueno) {
    base.push({ ruta: "usuarios", texto: "Usuarios y roles" });
  }
  return base;
});

const inicial = computed(() => (auth.usuario?.username?.[0] || "?").toUpperCase());

function ir(nombre) {
  abierto.value = false;
  router.push({ name: nombre });
}

async function salir() {
  abierto.value = false;
  await auth.cerrarSesion();
  carrito.limpiar();
  aviso("Sesión cerrada. ¡Vuelve pronto!", "exito");
  router.push({ name: "acceso" });
}
</script>

<template>
  <header class="cabecera">
    <RouterLink class="marca" :to="{ name: 'tienda' }" @click="abierto = false">
      <span class="marca-icono" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor"
             stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 11h4M8 9v4M15.5 11.5h.01M18 9.5h.01" />
          <path d="M17.5 6H6.5A4.5 4.5 0 0 0 2 10.5v3A4.5 4.5 0 0 0 6.5 18h11a4.5 4.5 0 0 0 4.5-4.5v-3A4.5 4.5 0 0 0 17.5 6Z" />
        </svg>
      </span>
      <span class="marca-texto">PIXEL<span>VAULT</span></span>
    </RouterLink>

    <div class="cabecera-acciones">
      <span class="usuario-chip">
        <span class="avatar">{{ inicial }}</span>
        <span class="usuario-info"><small>PLAYER</small><strong>{{ auth.usuario?.username }}</strong></span>
        <span :class="['rol', 'rol-' + auth.rol]">{{ auth.rol }}</span>
      </span>

      <button class="btn-menu" type="button" :aria-expanded="abierto" aria-label="Menú de navegación"
              @click="abierto = !abierto">
        <span class="btn-menu-barras" aria-hidden="true"><span></span><span></span><span></span></span>
      </button>

      <nav v-if="abierto" class="menu-principal">
        <button v-for="e in enlaces" :key="e.ruta" type="button" class="nav-enlace"
                :class="{ activo: route.name === e.ruta }" @click="ir(e.ruta)">
          {{ e.texto }}
          <span v-if="e.badge" class="nav-badge">{{ e.badge }}</span>
        </button>
        <span class="menu-sep" aria-hidden="true"></span>
        <button type="button" class="nav-enlace menu-salir" @click="salir">Salir</button>
      </nav>
    </div>
  </header>

  <div v-if="abierto" class="menu-fondo" @click="abierto = false"></div>
</template>
