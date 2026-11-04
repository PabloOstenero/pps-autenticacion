<script setup>
import { computed, onMounted, ref } from "vue";
import { solicitar } from "../api";
import { aviso } from "../avisos";

const pedidos = ref([]);
const cargando = ref(true);

const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });
const fecha = new Intl.DateTimeFormat("es-ES", { dateStyle: "medium", timeStyle: "short" });

const totalFacturado = computed(() => pedidos.value.reduce((s, p) => s + p.total, 0));

onMounted(async () => {
  try {
    pedidos.value = await solicitar("/admin/pedidos");
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
        <p class="eyebrow">// PANEL DEL EQUIPO</p>
        <h1>Pedidos de la tienda</h1>
        <p class="pagina-sub">Todos los pedidos de todos los clientes (staff / owner).</p>
      </div>
      <div class="kpi">
        <span class="kpi-num">{{ pedidos.length }}</span>
        <span class="kpi-label">pedidos</span>
      </div>
      <div class="kpi">
        <span class="kpi-num">{{ euros.format(totalFacturado) }}</span>
        <span class="kpi-label">facturado</span>
      </div>
    </header>

    <p v-if="cargando" class="vacio">Cargando pedidos…</p>
    <p v-else-if="!pedidos.length" class="vacio">Todavía no hay pedidos en la tienda.</p>

    <table v-else class="tabla">
      <thead>
        <tr>
          <th>#</th><th>Cliente</th><th>Artículos</th><th>Fecha</th><th>Estado</th><th class="der">Total</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in pedidos" :key="p.id">
          <td class="mono">{{ p.id }}</td>
          <td>{{ p.usuario }}</td>
          <td>{{ p.num_articulos }}</td>
          <td>{{ fecha.format(new Date(p.fecha)) }}</td>
          <td><span :class="['estado', 'estado-' + p.estado]">{{ p.estado }}</span></td>
          <td class="der mono">{{ euros.format(p.total) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
