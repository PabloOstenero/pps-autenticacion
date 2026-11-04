<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { solicitar } from "../api";
import { useCarritoStore } from "../stores/carrito";
import { aviso } from "../avisos";

const carrito = useCarritoStore();
const router = useRouter();
const comprando = ref(false);

const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });

onMounted(() => carrito.cargar());

async function cambiar(item, delta) {
  const nueva = item.cantidad + delta;
  if (nueva < 1) return;
  try {
    await carrito.cambiarCantidad(item.videojuego_id, nueva);
  } catch (err) {
    aviso(err.message, "error");
    carrito.cargar();
  }
}

async function quitar(item) {
  try {
    await carrito.quitar(item.videojuego_id);
    aviso("Artículo eliminado del carrito", "info");
  } catch (err) {
    aviso(err.message, "error");
  }
}

async function vaciar() {
  try {
    await carrito.vaciar();
    aviso("Carrito vaciado", "info");
  } catch (err) {
    aviso(err.message, "error");
  }
}

async function comprar() {
  comprando.value = true;
  try {
    const pedido = await solicitar("/pedidos", { metodo: "POST" });
    await carrito.cargar();
    aviso(`¡Compra realizada! Pedido #${pedido.id}`, "exito");
    router.push({ name: "pedidos" });
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    comprando.value = false;
  }
}
</script>

<template>
  <section class="pagina">
    <header class="pagina-cab">
      <div>
        <p class="eyebrow">// TU MOCHILA</p>
        <h1>Carrito de compra</h1>
      </div>
      <button v-if="carrito.numArticulos" class="boton fantasma" type="button" @click="vaciar">Vaciar</button>
    </header>

    <div v-if="!carrito.numArticulos" class="vacio-panel">
      <p class="vacio">Tu carrito está vacío. Ve a la tienda y añade algo épico.</p>
      <RouterLink class="boton primario" :to="{ name: 'tienda' }">Ir a la tienda</RouterLink>
    </div>

    <div v-else class="carrito-disposicion">
      <ul class="lista-carrito">
        <li v-for="item in carrito.items" :key="item.videojuego_id" class="linea-carrito">
          <div class="linea-info">
            <strong>{{ item.titulo }}</strong>
            <span class="linea-unitario">{{ euros.format(item.precio_unitario) }} / ud.</span>
          </div>
          <div class="cantidad">
            <button type="button" aria-label="Quitar uno" @click="cambiar(item, -1)">−</button>
            <span>{{ item.cantidad }}</span>
            <button type="button" aria-label="Añadir uno" @click="cambiar(item, 1)">＋</button>
          </div>
          <span class="linea-subtotal">{{ euros.format(item.subtotal) }}</span>
          <button class="boton basura" type="button" aria-label="Eliminar" @click="quitar(item)">✕</button>
        </li>
      </ul>

      <aside class="resumen-compra">
        <h2>Resumen</h2>
        <div class="fila"><span>Artículos</span><span>{{ carrito.numArticulos }}</span></div>
        <div class="fila total"><span>Total</span><span>{{ euros.format(carrito.total) }}</span></div>
        <button class="boton primario grande" type="button" :disabled="comprando" @click="comprar">
          {{ comprando ? "Procesando…" : "▶ Finalizar compra" }}
        </button>
      </aside>
    </div>
  </section>
</template>
