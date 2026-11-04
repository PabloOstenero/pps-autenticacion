<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { solicitar } from "../api";
import { useAuthStore } from "../stores/auth";
import { useCarritoStore } from "../stores/carrito";
import { aviso } from "../avisos";

const auth = useAuthStore();
const carrito = useCarritoStore();

const juegos = ref([]);
const cargando = ref(true);
const filtros = reactive({ buscar: "", plataforma: "", orden: "titulo", disponibles: false });

const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });
const plataformas = ["PC", "PS5", "Xbox Series", "Switch", "Multiplataforma"];
const CLASE = { PC: "p-pc", PS5: "p-ps5", "Xbox Series": "p-xbox", Switch: "p-switch", Multiplataforma: "p-multi" };

const resumen = computed(() =>
  juegos.value.length === 1 ? "1 juego en catálogo" : `${juegos.value.length} juegos en catálogo`
);

async function cargarCatalogo() {
  cargando.value = true;
  const params = new URLSearchParams();
  if (filtros.buscar) params.set("buscar", filtros.buscar);
  if (filtros.plataforma) params.set("plataforma", filtros.plataforma);
  params.set("orden", filtros.orden);
  if (filtros.disponibles) params.set("disponibles", "true");
  try {
    juegos.value = await solicitar(`/videojuegos?${params}`, { auth: false });
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    cargando.value = false;
  }
}

async function anadir(juego) {
  try {
    await carrito.anadir(juego.id);
    aviso("¡Añadido al carrito!", "exito");
  } catch (err) {
    aviso(err.message, "error");
  }
}

let temporizador;
watch(() => filtros.buscar, () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(cargarCatalogo, 300);
});
watch([() => filtros.plataforma, () => filtros.orden, () => filtros.disponibles], cargarCatalogo);

onMounted(cargarCatalogo);
</script>

<template>
  <section class="pagina">
    <div class="hero">
      <div class="hero-texto">
        <p class="eyebrow">// CATÁLOGO EN VIVO</p>
        <h1>Tu próxima <span class="grad">obsesión</span> empieza aquí</h1>
        <p class="hero-sub">Explora, añade y compra al instante. Sin fricción, puro juego.</p>
      </div>
      <div class="hero-meta">
        <span class="pulso" aria-hidden="true"></span>
        <span>{{ cargando ? "Cargando catálogo…" : resumen }}</span>
      </div>
    </div>

    <form class="barra-filtros" @submit.prevent="cargarCatalogo">
      <div class="campo-buscar">
        <span class="lupa" aria-hidden="true">⌕</span>
        <input v-model="filtros.buscar" type="search" placeholder="Busca tu próximo juego…" />
      </div>
      <select v-model="filtros.plataforma" aria-label="Plataforma">
        <option value="">Todas</option>
        <option v-for="p in plataformas" :key="p">{{ p }}</option>
      </select>
      <select v-model="filtros.orden" aria-label="Orden">
        <option value="titulo">A → Z</option>
        <option value="precio_asc">Precio ↑</option>
        <option value="precio_desc">Precio ↓</option>
      </select>
      <label class="interruptor">
        <input v-model="filtros.disponibles" type="checkbox" />
        <span>Solo con stock</span>
      </label>
      <button type="submit" class="boton">Filtrar</button>
    </form>

    <div v-if="cargando" class="grid-catalogo"><p class="vacio">Cargando catálogo…</p></div>
    <div v-else-if="!juegos.length" class="grid-catalogo">
      <p class="vacio">No hay juegos que cumplan esos filtros… prueba otra búsqueda.</p>
    </div>
    <div v-else class="grid-catalogo">
      <article v-for="(j, i) in juegos" :key="j.id" class="tarjeta-juego" :style="{ animationDelay: `${i * 45}ms` }">
        <div class="tarjeta-cab">
          <span :class="['chip', CLASE[j.plataforma] || 'p-multi']">{{ j.plataforma }}</span>
          <span v-if="j.fecha_lanzamiento" class="anio">{{ String(j.fecha_lanzamiento).slice(0, 4) }}</span>
        </div>
        <h3>{{ j.titulo }}</h3>
        <p class="categoria">{{ j.categoria }}</p>
        <p class="desc">{{ j.descripcion || "Sin descripción." }}</p>
        <div class="pie">
          <span class="precio">{{ euros.format(j.precio) }}</span>
          <span :class="['stock', { agotado: j.stock === 0 }]">{{ j.stock === 0 ? "Agotado" : `${j.stock} ud.` }}</span>
        </div>
        <button class="boton-anadir" :disabled="j.stock === 0" @click="anadir(j)">
          {{ j.stock === 0 ? "Sin stock" : "＋ Añadir" }}
        </button>
      </article>
    </div>

    <p v-if="auth.esGestor" class="pista-centro">
      ¿Eres del equipo? <RouterLink :to="{ name: 'publicar' }">Publica un juego nuevo</RouterLink>.
    </p>
  </section>
</template>
