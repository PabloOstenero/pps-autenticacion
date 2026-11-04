<script setup>
import { onMounted, ref } from "vue";
import { solicitar } from "../api";
import { aviso } from "../avisos";

const pedidos = ref([]);
const cargando = ref(true);

const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });
const fecha = new Intl.DateTimeFormat("es-ES", { dateStyle: "medium", timeStyle: "short" });

onMounted(async () => {
  try {
    pedidos.value = await solicitar("/pedidos");
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    cargando.value = false;
  }
});
</script>

<template>
  <section class="pagina">
    <header class="pagina-cab">
      <div>
        <p class="eyebrow">// HISTORIAL</p>
        <h1>Mis pedidos</h1>
      </div>
    </header>

    <p v-if="cargando" class="vacio">Cargando pedidos…</p>
    <div v-else-if="!pedidos.length" class="vacio-panel">
      <p class="vacio">Todavía no has hecho ningún pedido.</p>
      <RouterLink class="boton primario" :to="{ name: 'tienda' }">Ir a la tienda</RouterLink>
    </div>

    <ul v-else class="lista-pedidos">
      <li v-for="p in pedidos" :key="p.id" class="pedido">
        <header class="pedido-cab">
          <span class="pedido-id">Pedido #{{ p.id }}</span>
          <span :class="['estado', 'estado-' + p.estado]">{{ p.estado }}</span>
          <span class="pedido-fecha">{{ fecha.format(new Date(p.fecha)) }}</span>
        </header>
        <ul class="pedido-items">
          <li v-for="it in p.items" :key="it.videojuego_id">
            <span>{{ it.cantidad }} × {{ it.titulo }}</span>
            <span>{{ euros.format(it.subtotal) }}</span>
          </li>
        </ul>
        <footer class="pedido-pie">
          <span>{{ p.num_articulos }} artículo(s)</span>
          <strong>{{ euros.format(p.total) }}</strong>
        </footer>
      </li>
    </ul>
  </section>
</template>
