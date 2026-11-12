import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "./stores/auth";

const rutas = [
  { path: "/", redirect: { name: "tienda" } },
  { path: "/acceso", name: "acceso", component: () => import("./views/AccesoView.vue"), meta: { publico: true } },
  { path: "/tienda", name: "tienda", component: () => import("./views/TiendaView.vue") },
  { path: "/carrito", name: "carrito", component: () => import("./views/CarritoView.vue") },
  { path: "/pedidos", name: "pedidos", component: () => import("./views/PedidosView.vue") },
  { path: "/publicar", name: "publicar", component: () => import("./views/PublicarView.vue"), meta: { gestor: true } },
  { path: "/pedidos-tienda", name: "pedidos-tienda", component: () => import("./views/PedidosTiendaView.vue"), meta: { gestor: true } },
  { path: "/usuarios", name: "usuarios", component: () => import("./views/UsuariosView.vue"), meta: { dueno: true } },
  { path: "/:pathMatch(.*)*", redirect: { name: "tienda" } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes: rutas,
  scrollBehavior: () => ({ top: 0 }),
});

// Guardas de navegación: reflejan el RBAC del backend (que es la autoridad real).
router.beforeEach((destino) => {
  const auth = useAuthStore();
  if (destino.meta.publico) {
    return auth.autenticado ? { name: "tienda" } : true;
  }
  if (!auth.autenticado) return { name: "acceso" };
  if (destino.meta.gestor && !auth.esGestor) return { name: "tienda" };
  if (destino.meta.dueno && !auth.esDueno) return { name: "tienda" };
  return true;
});

export default router;
