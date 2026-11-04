"""Prueba de humo / verificación de la API REST (FastAPI + JWT).

Cubre las características pedidas para la aplicación distribuida:

1. API REST con framework Python (FastAPI).
2. Registro de usuarios con contraseñas HASHEADAS (bcrypt).
3. Sistema de roles (3): owner (administrador), staff (gestor), client (cliente),
   con control de acceso (RBAC) y aislamiento entre usuarios.
4. JWT como autenticación: access token + REFRESCO con rotación, detección de
   reuso y revocación.
5. CORS habilitado para el frontend separado (Vue).
6. Backend y frontend SEPARADOS (el backend ya no sirve el frontend).

Usa `Authorization: Bearer <access_token>`. No necesita cookies.
"""

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
ORIGEN_FRONT = "http://localhost:5173"
fallos = []


def pedir(metodo, ruta, cuerpo=None, token=None, cabeceras_extra=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    if cabeceras_extra:
        cabeceras.update(cabeceras_extra)
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, _cuerpo(resp), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, _cuerpo(e), dict(e.headers)


def _cuerpo(respuesta):
    datos = respuesta.read()
    if not datos:
        return None
    try:
        return json.loads(datos)
    except json.JSONDecodeError:
        return datos.decode("utf-8", "replace")


def comprobar(nombre, condicion, detalle=""):
    print(("OK  " if condicion else "FAIL") + f" {nombre} {detalle}")
    if not condicion:
        fallos.append(nombre)


def seccion(titulo):
    print(f"\n=== {titulo} ===")


def login(username, password):
    return pedir("POST", "/auth/login", {"username": username, "password": password})


def tiene(payload, *claves):
    return isinstance(payload, dict) and all(clave in payload for clave in claves)


# --------------------------------------------------------------------------- #
seccion("1. API pública")
# --------------------------------------------------------------------------- #
estado, cuerpo, _ = pedir("GET", "/salud")
comprobar("GET /salud", estado == 200 and cuerpo == {"estado": "ok"})

estado, lista, _ = pedir("GET", "/videojuegos")
comprobar("GET /videojuegos lista la semilla", estado == 200 and len(lista) >= 5, f"(recibidos: {len(lista)})")

estado, filtrados, _ = pedir("GET", "/videojuegos?plataforma=PC")
comprobar("filtro plataforma=PC", estado == 200 and filtrados and all(v["plataforma"] == "PC" for v in filtrados))

estado, buscados, _ = pedir("GET", "/videojuegos?buscar=celeste")
comprobar("buscar=celeste (case-insensitive)", estado == 200 and len(buscados) == 1)

# El backend ya NO sirve el frontend (están separados).
estado, _, _ = pedir("GET", "/app/")
comprobar("backend no sirve /app (frontend separado)", estado == 404)

# --------------------------------------------------------------------------- #
seccion("2. Registro de usuarios (contraseñas hasheadas)")
# --------------------------------------------------------------------------- #
nombre = f"tester{time.time_ns() % 10**9}"
estado, r, _ = pedir("POST", "/auth/registro", {"username": nombre, "password": "secreta123"})
TOKEN = r.get("access_token") if isinstance(r, dict) else None
comprobar("registro -> 201 y rol 'client' por defecto",
          estado == 201 and tiene(r, "access_token", "refresh_token", "usuario") and r["usuario"]["rol"] == "client")

estado, _, _ = pedir("POST", "/auth/registro", {"username": nombre, "password": "secreta123"})
comprobar("registro duplicado -> 409", estado == 409)
estado, _, _ = pedir("POST", "/auth/registro", {"username": "ab", "password": "corta"})
comprobar("registro inválido -> 422", estado == 422)

mostrar = json.dumps(r) if isinstance(r, dict) else ""
comprobar("la respuesta NO contiene la contraseña ni su hash",
          "secreta123" not in mostrar and "hash" not in mostrar.lower())

# --------------------------------------------------------------------------- #
seccion("3. Login y roles")
# --------------------------------------------------------------------------- #
estado, owner, _ = login("owner", "owner1234")
estado2, staff, _ = login("staff", "staff1234")
estado3, client, _ = login("client", "client1234")
TOKEN_OWNER = owner.get("access_token")
TOKEN_STAFF = staff.get("access_token")
TOKEN_CLIENT = client.get("access_token")
comprobar("login owner -> rol owner", estado == 200 and owner["usuario"]["rol"] == "owner")
comprobar("login staff -> rol staff", estado2 == 200 and staff["usuario"]["rol"] == "staff")
comprobar("login client -> rol client", estado3 == 200 and client["usuario"]["rol"] == "client")
estado, _, _ = pedir("POST", "/auth/login", {"username": "owner", "password": "mal"})
comprobar("login con clave incorrecta -> 401", estado == 401)

estado, yo, _ = pedir("GET", "/auth/me", token=TOKEN)
comprobar("GET /auth/me", estado == 200 and yo["username"] == nombre and yo["rol"] == "client")
estado, _, _ = pedir("GET", "/auth/me")
comprobar("GET /auth/me sin token -> 401", estado == 401)

# --------------------------------------------------------------------------- #
seccion("4. JWT: separación access / refresh y REFRESCO con rotación")
# --------------------------------------------------------------------------- #
comprobar("login devuelve access_token y refresh_token",
          tiene(owner, "access_token", "refresh_token") and owner.get("token_type") == "bearer")

# El refresh token NO vale como access token.
estado, _, _ = pedir("GET", "/auth/me", token=owner["refresh_token"])
comprobar("refresh token usado como access -> 401", estado == 401)
# El access token NO vale para refrescar.
estado, _, _ = pedir("POST", "/auth/refresh", {"refresh_token": owner["access_token"]})
comprobar("access token usado en /auth/refresh -> 401", estado == 401)
# Token corrupto.
estado, _, _ = pedir("POST", "/auth/refresh", {"refresh_token": "no-es-un-jwt"})
comprobar("refresh token corrupto -> 401", estado == 401)

# Flujo de refresco con rotación (usuario desechable para no afectar a los demás).
rc = f"refrescos{time.time_ns() % 10**9}"
_, rc_reg, _ = pedir("POST", "/auth/registro", {"username": rc, "password": "secreta123"})
R1 = rc_reg["refresh_token"]
A1 = rc_reg["access_token"]

estado, par2, _ = pedir("POST", "/auth/refresh", {"refresh_token": R1})
A2, R2 = par2.get("access_token"), par2.get("refresh_token")
comprobar("refresh con token válido -> 200 y par nuevo",
          estado == 200 and A2 and R2 and R2 != R1)
estado, yo_rc, _ = pedir("GET", "/auth/me", token=A2)
comprobar("el nuevo access token funciona", estado == 200 and yo_rc["username"] == rc)

# Reusar el refresh YA rotado -> 401 y revoca todas las sesiones (antirrobo).
estado, cuerpo_reuso, _ = pedir("POST", "/auth/refresh", {"refresh_token": R1})
comprobar("reuso de refresh rotado -> 401 (detección de robo)", estado == 401)
estado, _, _ = pedir("POST", "/auth/refresh", {"refresh_token": R2})
comprobar("tras el reuso, el refresh vigente también queda revocado -> 401", estado == 401)
# Un access token sigue siendo válido hasta caducar (es de vida corta).
estado, _, _ = pedir("GET", "/auth/me", token=A2)
comprobar("el access token no se revoca (caduca solo)", estado == 200)

# Logout revoca el refresh presentado.
_, cl2, _ = login("client", "client1234")
estado, _, _ = pedir("POST", "/auth/logout", {"refresh_token": cl2["refresh_token"]})
comprobar("logout -> 204", estado == 204)
estado, _, _ = pedir("POST", "/auth/refresh", {"refresh_token": cl2["refresh_token"]})
comprobar("refresh tras logout -> 401", estado == 401)
_, cl_re, _ = login("client", "client1234")
TOKEN_CLIENT = cl_re["access_token"]

# --------------------------------------------------------------------------- #
seccion("5. CORS (frontend separado)")
# --------------------------------------------------------------------------- #
estado, _, cabeceras = pedir("OPTIONS", "/auth/login", cabeceras_extra={
    "Origin": ORIGEN_FRONT,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "authorization,content-type",
})
allow_origin = cabeceras.get("access-control-allow-origin")
comprobar("preflight CORS permite el origen del frontend",
          estado in (200, 204) and allow_origin in (ORIGEN_FRONT, "*"), f"(allow-origin: {allow_origin})")

estado, _, cabeceras = pedir("GET", "/videojuegos", cabeceras_extra={"Origin": ORIGEN_FRONT})
comprobar("respuesta normal incluye Access-Control-Allow-Origin",
          cabeceras.get("access-control-allow-origin") in (ORIGEN_FRONT, "*"))

# --------------------------------------------------------------------------- #
seccion("6. Sin sesión -> 401")
# --------------------------------------------------------------------------- #
for ruta, met in [("/carrito", "GET"), ("/pedidos", "GET"), ("/admin/usuarios", "GET"),
                  ("/admin/pedidos", "GET"), ("/videojuegos", "POST")]:
    estado, _, _ = pedir(met, ruta, {} if met == "POST" else None)
    comprobar(f"{met} {ruta} sin token -> 401", estado == 401)

# --------------------------------------------------------------------------- #
seccion("7. RBAC — client: no toca catálogo ni datos ajenos")
# --------------------------------------------------------------------------- #
juego = {"titulo": "Stardew Valley", "plataforma": "PC", "categoria": "Simulación",
         "precio": 14.99, "stock": 3, "descripcion": "Granja y pueblo."}
INEXISTENTE = 999999

estado, _, _ = pedir("POST", "/videojuegos", juego, token=TOKEN)
comprobar("client POST /videojuegos -> 403", estado == 403)
estado, _, _ = pedir("PUT", f"/videojuegos/{INEXISTENTE}", {"precio": 1.0}, token=TOKEN)
comprobar("client PUT /videojuegos -> 403", estado == 403)
estado, _, _ = pedir("DELETE", f"/videojuegos/{INEXISTENTE}", token=TOKEN)
comprobar("client DELETE /videojuegos -> 403", estado == 403)
estado, _, _ = pedir("GET", "/admin/usuarios", token=TOKEN)
comprobar("client GET /admin/usuarios -> 403 (no ve a otros usuarios)", estado == 403)
estado, _, _ = pedir("GET", "/admin/pedidos", token=TOKEN)
comprobar("client GET /admin/pedidos -> 403 (no ve pedidos ajenos)", estado == 403)

# --------------------------------------------------------------------------- #
seccion("8. RBAC — staff: gestiona catálogo, no borra ni administra")
# --------------------------------------------------------------------------- #
estado, creado, _ = pedir("POST", "/videojuegos", juego, token=TOKEN_STAFF)
comprobar("staff POST /videojuegos -> 201", estado == 201 and creado["id"] > 0, f"(id={creado.get('id')})")
id_nuevo = creado["id"]
estado, actualizado, _ = pedir("PUT", f"/videojuegos/{id_nuevo}", {"precio": 11.99, "stock": 10}, token=TOKEN_STAFF)
comprobar("staff PUT /videojuegos -> 200", estado == 200 and actualizado["precio"] == 11.99)
estado, _, _ = pedir("DELETE", f"/videojuegos/{id_nuevo}", token=TOKEN_STAFF)
comprobar("staff DELETE /videojuegos -> 403 (solo el dueño borra)", estado == 403)
estado, _, _ = pedir("GET", "/admin/usuarios", token=TOKEN_STAFF)
comprobar("staff GET /admin/usuarios -> 403", estado == 403)
estado, _, _ = pedir("GET", "/admin/pedidos", token=TOKEN_STAFF)
comprobar("staff GET /admin/pedidos -> 200", estado == 200)

# --------------------------------------------------------------------------- #
seccion("9. RBAC — owner: administra usuarios y roles (con salvaguardas)")
# --------------------------------------------------------------------------- #
estado, usuarios, _ = pedir("GET", "/admin/usuarios", token=TOKEN_OWNER)
nombres = {u["username"] for u in usuarios} if isinstance(usuarios, list) else set()
comprobar("owner GET /admin/usuarios -> 200", estado == 200 and {"owner", "staff", "client"} <= nombres,
          f"({len(usuarios) if isinstance(usuarios, list) else '?'} usuarios)")

estado, _, _ = pedir("PATCH", "/admin/usuarios/9999/rol", {"rol": "staff"}, token=TOKEN_OWNER)
comprobar("owner cambia rol de inexistente -> 404", estado == 404)
estado, _, _ = pedir("PATCH", "/admin/usuarios/owner/rol", {"rol": "client"}, token=TOKEN_OWNER)
comprobar("owner no puede degradarse a sí mismo -> 409", estado == 409)
estado, _, _ = pedir("DELETE", "/admin/usuarios/owner", token=TOKEN_OWNER)
comprobar("owner no puede eliminarse a sí mismo -> 409", estado == 409)

estado, asc, _ = pedir("PATCH", f"/admin/usuarios/{nombre}/rol", {"rol": "staff"}, token=TOKEN_OWNER)
comprobar("owner asciende client -> staff", estado == 200 and asc["rol"] == "staff")
estado, _, _ = pedir("POST", "/videojuegos", {**juego, "titulo": "Hades"}, token=TOKEN)
comprobar("el rol nuevo tiene efecto inmediato (ya puede crear) -> 201", estado == 201)

# --------------------------------------------------------------------------- #
seccion("10. Carrito y pedidos propios + aislamiento entre clientes")
# --------------------------------------------------------------------------- #
estado, carrito, _ = pedir("POST", f"/carrito?videojuego_id={id_nuevo}&cantidad=2", token=TOKEN_CLIENT)
comprobar("client añade al carrito", estado == 201 and carrito["num_articulos"] == 2)
estado, carrito, _ = pedir("PATCH", f"/carrito/{id_nuevo}?cantidad=1", token=TOKEN_CLIENT)
comprobar("client cambia cantidad", estado == 200 and carrito["num_articulos"] == 1 and carrito["total"] == 11.99)
estado, _, _ = pedir("POST", f"/carrito?videojuego_id={id_nuevo}&cantidad=99", token=TOKEN_CLIENT)
comprobar("client sin stock -> 409", estado == 409)
estado, pedido, _ = pedir("POST", "/pedidos", token=TOKEN_CLIENT)
comprobar("client compra -> 201", estado == 201 and pedido["usuario"] == "client" and pedido["total"] == 11.99)
estado, carrito, _ = pedir("GET", "/carrito", token=TOKEN_CLIENT)
comprobar("carrito vacío tras comprar", carrito["num_articulos"] == 0)

estado, todos, _ = pedir("GET", "/admin/pedidos", token=TOKEN_STAFF)
comprobar("staff ve el pedido en la lista de la tienda", estado == 200 and any(p["id"] == pedido["id"] for p in todos))

otro = f"otro{time.time_ns() % 10**9}"
_, r2, _ = pedir("POST", "/auth/registro", {"username": otro, "password": "secreta456"})
TOKEN_OTRO = r2.get("access_token")
estado, c2, _ = pedir("GET", "/carrito", token=TOKEN_OTRO)
comprobar("otro cliente ve su carrito vacío", estado == 200 and c2["num_articulos"] == 0)
estado, p2, _ = pedir("GET", "/pedidos", token=TOKEN_OTRO)
comprobar("otro cliente no ve mis pedidos", estado == 200 and len(p2) == 0)
estado, _, _ = pedir("GET", f"/pedidos/{pedido['id']}", token=TOKEN_OTRO)
comprobar("otro cliente no accede a mi pedido -> 404", estado == 404)

# --------------------------------------------------------------------------- #
seccion("11. Limpieza (owner)")
# --------------------------------------------------------------------------- #
estado, _, _ = pedir("DELETE", f"/videojuegos/{id_nuevo}", token=TOKEN_OWNER)
comprobar("owner DELETE /videojuegos/{id} -> 204", estado == 204)
estado, _, _ = pedir("DELETE", f"/videojuegos/{INEXISTENTE}", token=TOKEN_OWNER)
comprobar("DELETE videojuego inexistente -> 404", estado == 404)
estado, _, _ = pedir("DELETE", f"/admin/usuarios/{otro}", token=TOKEN_OWNER)
comprobar("owner elimina usuario -> 204", estado == 204)
estado, _, _ = pedir("DELETE", f"/admin/usuarios/{otro}", token=TOKEN_OWNER)
comprobar("eliminar usuario inexistente -> 404", estado == 404)

# --------------------------------------------------------------------------- #
print(f"\n{len(fallos)} fallo(s): {fallos}" if fallos else "\nTodas las comprobaciones han pasado.")
raise SystemExit(1 if fallos else 0)
