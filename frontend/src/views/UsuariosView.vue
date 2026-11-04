<script setup>
import { onMounted, ref } from "vue";
import { solicitar } from "../api";
import { useAuthStore } from "../stores/auth";
import { aviso } from "../avisos";

const auth = useAuthStore();
const usuarios = ref([]);
const cargando = ref(true);
const roles = ["client", "staff", "owner"];

async function cargar() {
  try {
    usuarios.value = await solicitar("/admin/usuarios");
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    cargando.value = false;
  }
}

async function cambiarRol(usuario, nuevoRol) {
  if (nuevoRol === usuario.rol) return;
  try {
    const actualizado = await solicitar(`/admin/usuarios/${usuario.username}/rol`, {
      metodo: "PATCH",
      cuerpo: { rol: nuevoRol },
    });
    Object.assign(usuario, actualizado);
    aviso(`Rol de ${usuario.username} → ${nuevoRol}`, "exito");
  } catch (err) {
    aviso(err.message, "error");
    cargar();
  }
}

async function eliminar(usuario) {
  if (!confirm(`¿Eliminar al usuario «${usuario.username}»? Esta acción no se puede deshacer.`)) return;
  try {
    await solicitar(`/admin/usuarios/${usuario.username}`, { metodo: "DELETE" });
    usuarios.value = usuarios.value.filter((u) => u.username !== usuario.username);
    aviso(`Usuario ${usuario.username} eliminado`, "info");
  } catch (err) {
    aviso(err.message, "error");
  }
}

onMounted(cargar);
</script>

<template>
  <section class="pagina">
    <header class="pagina-cab">
      <div>
        <p class="eyebrow">// SOLO DUEÑO</p>
        <h1>Usuarios y roles</h1>
        <p class="pagina-sub">Cambia roles o elimina cuentas. No puedes degradarte ni eliminarte a ti mismo.</p>
      </div>
      <div class="kpi">
        <span class="kpi-num">{{ usuarios.length }}</span>
        <span class="kpi-label">usuarios</span>
      </div>
    </header>

    <p v-if="cargando" class="vacio">Cargando usuarios…</p>

    <table v-else class="tabla">
      <thead>
        <tr><th>Usuario</th><th>Rol</th><th>Alta</th><th class="der">Acciones</th></tr>
      </thead>
      <tbody>
        <tr v-for="u in usuarios" :key="u.username">
          <td>
            <strong>{{ u.username }}</strong>
            <span v-if="u.username === auth.usuario?.username" class="tu">tú</span>
          </td>
          <td>
            <select :value="u.rol"
                    :disabled="u.username === auth.usuario?.username"
                    @change="cambiarRol(u, $event.target.value)">
              <option v-for="r in roles" :key="r">{{ r }}</option>
            </select>
          </td>
          <td>{{ new Date(u.creado).toLocaleDateString("es-ES") }}</td>
          <td class="der">
            <button class="boton basura" type="button"
                    :disabled="u.username === auth.usuario?.username"
                    @click="eliminar(u)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
