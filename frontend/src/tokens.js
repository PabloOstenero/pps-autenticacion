/* Gestión de tokens.
 *
 * Se guardan en `localStorage` para sobrevivir a las recargas del navegador.
 * Consecuencia de seguridad: si un atacante logra inyectar JavaScript (XSS),
 * podría leerlos. Es el compromiso habitual en SPAs que consumen una API en
 * otro origen. La alternativa más segura en producción es guardar los tokens en
 * cookies **httpOnly** emitidas por un BFF del mismo origen (así el JS nunca
 * los ve), o servir el frontend detrás de un proxy inverso en el mismo sitio.
 *
 * Nota: guardar el access token evita que CADA recarga dispare un refresco
 * (y por tanto una rotación) del refresh token; solo se refresca cuando el
 * access token realmente caduca.
 */

const CLAVE_ACCESS = "pv_access_token";
const CLAVE_REFRESH = "pv_refresh_token";

export function obtenerAccess() {
  return localStorage.getItem(CLAVE_ACCESS);
}

export function obtenerRefresh() {
  return localStorage.getItem(CLAVE_REFRESH);
}

export function guardarTokens(access, refresh) {
  if (access) localStorage.setItem(CLAVE_ACCESS, access);
  if (refresh) localStorage.setItem(CLAVE_REFRESH, refresh);
}

export function limpiarTokens() {
  localStorage.removeItem(CLAVE_ACCESS);
  localStorage.removeItem(CLAVE_REFRESH);
}
