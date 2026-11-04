<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { solicitar } from "../api";
import { aviso } from "../avisos";

const router = useRouter();
const enviando = ref(false);

const plataformas = ["PC", "PS5", "Xbox Series", "Switch", "Multiplataforma"];

const juego = reactive({
  titulo: "",
  plataforma: "Multiplataforma",
  categoria: "",
  precio: 19.99,
  stock: 10,
  descripcion: "",
  fecha_lanzamiento: "",
});

async function publicar() {
  enviando.value = true;
  try {
    const cuerpo = {
      titulo: juego.titulo,
      plataforma: juego.plataforma,
      categoria: juego.categoria,
      precio: Number(juego.precio),
      stock: Number(juego.stock),
      descripcion: juego.descripcion || null,
      fecha_lanzamiento: juego.fecha_lanzamiento || null,
    };
    const creado = await solicitar("/videojuegos", { metodo: "POST", cuerpo });
    aviso(`Juego «${creado.titulo}» publicado (id ${creado.id})`, "exito");
    router.push({ name: "tienda" });
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <section class="pagina">
    <header class="pagina-cab">
      <div>
        <p class="eyebrow">// PANEL DEL EQUIPO</p>
        <h1>Publicar un juego</h1>
        <p class="pagina-sub">Disponible para <strong>staff</strong> y <strong>owner</strong>.</p>
      </div>
    </header>

    <form class="form-panel" @submit.prevent="publicar">
      <label class="ancho">Título
        <input v-model.trim="juego.titulo" required maxlength="150" placeholder="Hollow Knight" />
      </label>

      <label>Plataforma
        <select v-model="juego.plataforma" required>
          <option v-for="p in plataformas" :key="p">{{ p }}</option>
        </select>
      </label>

      <label>Categoría
        <input v-model.trim="juego.categoria" required maxlength="50" placeholder="Metroidvania" />
      </label>

      <label>Precio (€)
        <input v-model.number="juego.precio" type="number" min="0" step="0.01" required />
      </label>

      <label>Stock
        <input v-model.number="juego.stock" type="number" min="0" step="1" required />
      </label>

      <label>Fecha de lanzamiento (opcional)
        <input v-model="juego.fecha_lanzamiento" type="date" />
      </label>

      <label class="ancho">Descripción
        <textarea v-model.trim="juego.descripcion" rows="3" maxlength="1000"
                  placeholder="Cuenta qué hace especial a este juego…"></textarea>
      </label>

      <div class="ancho acciones-form">
        <button type="submit" class="boton primario" :disabled="enviando">
          {{ enviando ? "Publicando…" : "✦ Publicar" }}
        </button>
        <RouterLink class="boton fantasma" :to="{ name: 'tienda' }">Cancelar</RouterLink>
      </div>
    </form>
  </section>
</template>
