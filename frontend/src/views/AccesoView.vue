<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useCarritoStore } from "../stores/carrito";
import { aviso } from "../avisos";

const auth = useAuthStore();
const carrito = useCarritoStore();
const router = useRouter();

const tab = ref("login");
const cargando = ref(false);

const login = ref({ username: "", password: "" });
const registro = ref({ username: "", password: "" });

async function entrar() {
  cargando.value = true;
  try {
    const usuario = await auth.iniciarSesion(login.value);
    await carrito.cargar();
    aviso(`¡Bienvenido, ${usuario.username}!`, "exito");
    router.push({ name: "tienda" });
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    cargando.value = false;
  }
}

async function crearCuenta() {
  cargando.value = true;
  try {
    await auth.registrar(registro.value);
    await carrito.cargar();
    aviso("Cuenta creada. ¡A jugar!", "exito");
    router.push({ name: "tienda" });
  } catch (err) {
    aviso(err.message, "error");
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <section class="vista-auth">
    <div class="auth-panel">
      <span class="auth-linea" aria-hidden="true"></span>
      <p class="eyebrow">// ACCESO AL SISTEMA</p>
      <h2 class="auth-title">Entra en la <span class="grad">arena</span></h2>
      <p class="auth-sub">Guarda tu carrito, sigue tus pedidos y domina el catálogo.</p>

      <div class="tabs" role="tablist">
        <button type="button" class="tab" :class="{ activo: tab === 'login' }" @click="tab = 'login'">Iniciar sesión</button>
        <button type="button" class="tab" :class="{ activo: tab === 'registro' }" @click="tab = 'registro'">Crear cuenta</button>
      </div>

      <form v-if="tab === 'login'" class="form-auth" @submit.prevent="entrar">
        <label>Usuario
          <input v-model.trim="login.username" autocomplete="username" placeholder="tu_nick" required />
        </label>
        <label>Contraseña
          <input v-model="login.password" type="password" autocomplete="current-password" placeholder="••••••••" required />
        </label>
        <button type="submit" class="boton primario" :disabled="cargando">▶ Entrar</button>
      </form>

      <form v-else class="form-auth" @submit.prevent="crearCuenta">
        <label>Usuario
          <input v-model.trim="registro.username" autocomplete="username" placeholder="tu_nick" required minlength="3"
                 pattern="[A-Za-z0-9_.\-]+" title="Letras, números, punto, guion y guion bajo" />
        </label>
        <label>Contraseña (mínimo 8 caracteres)
          <input v-model="registro.password" type="password" autocomplete="new-password" placeholder="••••••••" required minlength="8" />
        </label>
        <button type="submit" class="boton primario" :disabled="cargando">✦ Crear cuenta</button>
      </form>

      <p class="pista">Demo → <code>owner</code>/<code>owner1234</code> · <code>staff</code>/<code>staff1234</code> · <code>client</code>/<code>client1234</code></p>
    </div>
  </section>
</template>
