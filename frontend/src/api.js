/* Cliente HTTP de la API con REFRESCO AUTOMÁTICO de JWT.
 *
 * Cuando una petición devuelve 401 (access token caducado), se pide un nuevo
 * par de tokens a `/auth/refresh` y se reintenta la petición original. El
 * refresco es "single-flight": si llegan varias peticiones a la vez con el token
 * caducado, solo se lanza UN refresco y todas esperan al mismo.
 */

import { guardarTokens, limpiarTokens, obtenerAccess, obtenerRefresh } from "./tokens";

export const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

let refrescoEnCurso = null;
let alExpirar = null;

/** Registra un callback para cuando la sesión caduca definitivamente. */
export function alExpirarSesion(callback) {
  alExpirar = callback;
}

async function refrescar() {
  const refreshToken = obtenerRefresh();
  if (!refreshToken) throw new Error("No hay refresh token");
  if (refrescoEnCurso) return refrescoEnCurso;

  refrescoEnCurso = (async () => {
    const resp = await fetch(`${API}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!resp.ok) {
      limpiarTokens();
      throw new Error("No se pudo refrescar la sesión");
    }
    const datos = await resp.json();
    guardarTokens(datos.access_token, datos.refresh_token);
    return datos;
  })();

  try {
    return await refrescoEnCurso;
  } finally {
    refrescoEnCurso = null;
  }
}

function mensajeError(datos, estado) {
  if (datos && typeof datos === "object" && datos.detail) {
    if (Array.isArray(datos.detail)) {
      return datos.detail.map((e) => `${e.loc?.slice(-1)[0] ?? ""}: ${e.msg}`).join(" · ");
    }
    return String(datos.detail);
  }
  return `Error ${estado}`;
}

/**
 * Realiza una petición a la API.
 * @param {string} ruta  p.ej. "/videojuegos"
 * @param {{metodo?:string, cuerpo?:any, auth?:boolean, reintentar?:boolean}} opciones
 */
export async function solicitar(ruta, { metodo = "GET", cuerpo, auth = true, reintentar = true } = {}) {
  const cabeceras = {};
  if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";
  if (auth) {
    const access = obtenerAccess();
    if (access) cabeceras["Authorization"] = `Bearer ${access}`;
  }

  const resp = await fetch(`${API}${ruta}`, {
    method: metodo,
    headers: cabeceras,
    body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
  });

  // Access token caducado -> refrescamos y reintentamos una sola vez.
  if (resp.status === 401 && auth && reintentar && obtenerRefresh()) {
    try {
      await refrescar();
    } catch {
      if (alExpirar) alExpirar();
      throw new Error("Sesión caducada. Inicia sesión de nuevo.");
    }
    return solicitar(ruta, { metodo, cuerpo, auth, reintentar: false });
  }

  if (resp.status === 204) return null;

  let datos = null;
  try {
    datos = await resp.json();
  } catch {
    /* sin cuerpo */
  }

  if (!resp.ok) throw new Error(mensajeError(datos, resp.status));
  return datos;
}
