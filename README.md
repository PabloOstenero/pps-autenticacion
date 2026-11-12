# Pixel Vault — Tienda de Videojuegos (FastAPI + Vue 3)

Aplicación web **distribuida**: un **backend** de API REST con **FastAPI** y un
**frontend** separado con **Vue 3 + Vite**. Autenticación **JWT** (access + refresh
con rotación) y **control de acceso por roles** (RBAC).

Los datos se guardan **en memoria** (se pierden al reiniciar el servidor): no hace
falta base de datos ni persistencia.

## Características

| Requisito | Cómo se cumple |
| --------- | -------------- |
| Backend con framework Python | **FastAPI** (`app/`) |
| Frontend separado | **Vue 3 + Vite** en su propio proyecto (`frontend/`), consume la API por HTTP (CORS) |
| Registro de usuarios (claves seguras) | Hash **bcrypt** (nunca en claro); validación de contraseña mínima |
| Sistema de roles (mínimo 3) | **`owner`** (administrador), **`staff`** (gestor) y **`client`** (cliente), aplicados de verdad (RBAC en cada endpoint) |
| API REST con **JWT** | Access token + **refresh token con rotación, detección de reuso y revocación** |

## Estructura

```
PPS-tienda-prueba/
├── app/                     # BACKEND (FastAPI)
│   ├── main.py              # App, CORS, lifespan y montaje de routers
│   ├── models.py            # Esquemas Pydantic
│   ├── security.py          # bcrypt + JWT (access/refresh) + RBAC
│   ├── store.py             # Almacén en memoria (usuarios, catálogo, carrito, pedidos y refresh tokens)
│   └── routers/
│       ├── auth.py          # registro, login, refresh, logout, /me
│       ├── videojuegos.py   # CRUD del catálogo
│       ├── carrito.py       # Carrito de la compra
│       ├── pedidos.py       # Checkout y consulta de pedidos
│       └── admin.py         # Pedidos de la tienda y gestión de usuarios/roles
├── frontend/                # FRONTEND (Vue 3 + Vite)  ← proyecto independiente
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js          # arranque (Pinia + router)
│       ├── api.js           # cliente HTTP con refresco automático de JWT
│       ├── tokens.js        # almacenamiento de tokens
│       ├── router.js        # rutas + guardas por rol
│       ├── styles.css       # tema neón/synthwave
│       ├── components/      # cabecera + menú hamburguesa
│       └── views/           # una vista por "página"
├── .github/
│   └── workflows/
│       └── deploy-frontend.yml   # CI/CD: publica el frontend en GitHub Pages
├── requirements.txt
├── smoke_test.py            # 62 comprobaciones de la API
└── README.md
```

## Arranque

Necesitas **dos procesos**: backend y frontend.

### 1) Backend (FastAPI)

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Estado: http://127.0.0.1:8000/salud

> Los orígenes permitidos por CORS se configuran con `CORS_ORIGINS`
> (por defecto `http://localhost:5173,http://127.0.0.1:5173`).

### 2) Frontend (Vue 3 + Vite)

```bash
cd frontend
npm install
npm run dev
```

- Interfaz: **http://localhost:5173**

El frontend lee la URL de la API de `VITE_API_URL` (ver `frontend/.env.example`,
por defecto `http://127.0.0.1:8000`).

### Usuarios de demostración

| Usuario  | Contraseña   | Rol      | Puede hacer |
| -------- | ------------ | -------- | ----------- |
| `owner`  | `owner1234`  | `owner`  | Todo: catálogo (incluido borrar), usuarios/roles y pedidos de la tienda |
| `staff`  | `staff1234`  | `staff`  | Gestionar el catálogo (crear/editar) y ver los pedidos de la tienda; también compra |
| `client` | `client1234` | `client` | Comprar: catálogo, carrito y **solo sus** pedidos |

Las cuentas nuevas se registran con rol `client`.

## Despliegue

La aplicación está desplegada en producción con los dos componentes separados:

| Componente | Plataforma | URL |
| ---------- | ---------- | --- |
| **Frontend** | GitHub Pages | <https://pabloostenero.github.io/pps-autenticacion/> |
| **Backend (API)** | Render | <https://pps-autenticacion.onrender.com> |

- Swagger: <https://pps-autenticacion.onrender.com/docs>
- Estado: <https://pps-autenticacion.onrender.com/salud>
- Repositorio: <https://github.com/PabloOstenero/pps-autenticacion>

### Backend en Render

Servicio **Web Service** (Python 3) apuntando a la raíz del repositorio:

| Ajuste | Valor |
| ------ | ----- |
| Root Directory | *(raíz del repo)* |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/salud` |

Variables de entorno:

| Variable | Valor |
| -------- | ----- |
| `SECRET_KEY` | Clave aleatoria de 64 caracteres hex: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `CORS_ORIGINS` | `https://pabloostenero.github.io,http://localhost:5173` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `PYTHON_VERSION` | `3.13.0` |

> `SECRET_KEY` debe ser fija: si no se define, el backend genera una aleatoria en
> cada arranque y todas las sesiones se invalidan. Los datos se guardan en memoria,
> así que se reinician cuando el servicio se duerme (plan free) o se redepliega.

### Frontend en GitHub Pages

El despliegue es automático con GitHub Actions:

- Workflow: `.github/workflows/deploy-frontend.yml`
- Se ejecuta en cada push a `main` o manualmente desde **Actions → Run workflow**.
- Instala dependencias con `npm ci`, compila con `npm run build` y publica `frontend/dist`.
- `VITE_API_URL` se inyecta en el build: `https://pps-autenticacion.onrender.com`.
- En `frontend/vite.config.js`, `base: "/pps-autenticacion/"` para que los assets se
  sirvan bajo el subdirectorio del repositorio.
- El router usa **hash history** (`/#/tienda`), de modo que recargar una ruta funciona
  en GitHub Pages sin necesidad de rewrites en el servidor.
- Origen de Pages: **Settings → Pages → Build and deployment → GitHub Actions**.

### CORS

El frontend y el backend están en dominios distintos, así que el backend debe
permitir el origen del frontend:

```
CORS_ORIGINS=https://pabloostenero.github.io,http://localhost:5173
```

Es solo el origen (esquema + dominio), sin la ruta del repo ni barra final.

### Probar el despliegue

1. Abre <https://pabloostenero.github.io/pps-autenticacion/> → redirige a `/#/tienda`.
2. Inicia sesión con `owner` / `owner1234`.
3. Recarga la página en una ruta y comprueba que no da 404.
4. Comprueba la API en <https://pps-autenticacion.onrender.com/salud> y `/docs`.

## Autenticación: JWT con **access + refresh**

1. `POST /auth/registro` y `POST /auth/login` devuelven un **par de tokens**:
   - **access token** — vida corta (15 min). Se envía en cada petición como
     `Authorization: Bearer <access_token>`.
   - **refresh token** — vida larga (7 días). **Solo** sirve para pedir un nuevo
     access token en `POST /auth/refresh`.
2. El campo `tipo` del JWT (`access`/`refresh`) impide usar un refresh como access
   y viceversa.
3. **Rotación:** cada `/auth/refresh` invalida el refresh usado y emite uno nuevo.
   Cada refresh tiene un `jti` que el servidor registra.
4. **Detección de reuso:** si llega un refresh ya rotado (posible robo), se
   **revocan todas** las sesiones de ese usuario y se responde `401`.
5. **Revocación:** `POST /auth/logout` invalida el refresh presentado;
   `POST /auth/logout-todo` cierra todas las sesiones del usuario.
6. En el frontend, `api.js` **refresca automáticamente**: si una petición recibe
   `401`, pide un par nuevo y la reintenta. El refresco es *single-flight* (varias
   peticiones con el token caducado comparten un único refresco).

El rol se lee **siempre del almacén**, no del token: cambiar o revocar un rol
surte efecto de inmediato aunque el token siga siendo válido.

## Roles y permisos (RBAC)

| Acción                                              | `client` | `staff` | `owner` |
| --------------------------------------------------- | :------: | :-----: | :-----: |
| Ver catálogo (`GET /videojuegos*`)                  |    ✅    |   ✅    |   ✅    |
| Carrito y **pedidos propios**                       |    ✅    |   ✅    |   ✅    |
| Crear / editar videojuegos                          |    ❌    |   ✅    |   ✅    |
| **Borrar** videojuegos (destructivo)                |    ❌    |   ❌    |   ✅    |
| Ver pedidos de todos los clientes (`/admin/pedidos`) |    ❌    |   ✅    |   ✅    |
| Listar usuarios, cambiar rol, eliminar (`/admin/*`) |    ❌    |   ❌    |   ✅    |

- Sin sesión → **401**; rol insuficiente → **403**.
- Un `client` **nunca** ve el carrito ni los pedidos de otro: pedir el pedido de
  otra persona devuelve **404** (no revela que exista).
- El `owner` no puede quitarse su rol ni eliminarse a sí mismo, y la tienda **nunca
  se queda sin ningún dueño** (**409**).
- `security.py` define `requiere_roles(...)`, `SoloStaff` y `SoloOwner`.

### Decisiones de seguridad

- **Contraseñas** con hash **bcrypt** (nunca en claro ni reversibles).
- **JWT** firmado con `HS256`. Define `SECRET_KEY` por entorno en producción (si no,
  se genera una aleatoria en cada arranque).
- **Access token** de vida corta y **refresh token** largo, con **rotación**,
  **detección de reuso** y **revocación**.
- En el frontend, los tokens se guardan en `localStorage` (compromiso habitual en
  SPAs que consumen una API en otro origen). La alternativa más segura en
  producción es usar cookies **httpOnly** emitidas por un BFF del mismo origen
  (así el JavaScript nunca ve los tokens).
- El frontend escapa el texto que pinta (Vue lo hace por defecto) → evita XSS
  almacenado desde títulos/descripciones.

### Variables de entorno (backend)

| Variable                      | Por defecto                          | Descripción |
| ----------------------------- | ------------------------------------ | ----------- |
| `SECRET_KEY`                  | aleatoria                            | Clave de firma del JWT (fija en producción) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15`                                 | Validez del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                  | Validez del refresh token |
| `CORS_ORIGINS`                | `http://localhost:5173,http://127.0.0.1:5173` | Orígenes permitidos para el frontend |

## Endpoints

### Autenticación

| Método | Ruta                 | Descripción |
| ------ | -------------------- | ----------- |
| POST   | `/auth/registro`     | Crear cuenta e iniciar sesión (201; 409 si existe) |
| POST   | `/auth/login`        | Iniciar sesión → `{access_token, refresh_token, usuario}` |
| POST   | `/auth/refresh`      | Nuevo par de tokens rotando el refresh (401 si inválido/reutilizado) |
| POST   | `/auth/logout`       | Revoca el refresh presentado (204) |
| POST   | `/auth/logout-todo`  | Revoca todas las sesiones del usuario (204) |
| GET    | `/auth/me`           | Usuario autenticado (401 si no hay sesión) |

### Videojuegos

| Método | Ruta                | Auth        | Descripción |
| ------ | ------------------- | ----------- | ----------- |
| GET    | `/videojuegos`      | No          | Listar. Filtros: `plataforma`, `categoria`, `buscar`, `disponibles`, `orden`, `skip`, `limit` |
| GET    | `/videojuegos/{id}` | No          | Obtener uno (404) |
| POST   | `/videojuegos`      | staff/owner | Crear (201; 403 si el rol es insuficiente) |
| PUT    | `/videojuegos/{id}` | staff/owner | Actualizar campos enviados (404) |
| DELETE | `/videojuegos/{id}` | owner       | Eliminar (204/404). También lo quita de los carritos |

### Carrito (sesión; propio de cada usuario)

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| GET    | `/carrito` | Ver artículos, total y número de artículos |
| POST   | `/carrito?videojuego_id=&cantidad=` | Añadir o acumular (404/409 sin stock) |
| PATCH  | `/carrito/{id}?cantidad=` | Cambiar cantidad (0 elimina) |
| DELETE | `/carrito/{id}` | Quitar un artículo (404) |
| DELETE | `/carrito` | Vaciar |

### Pedidos (sesión; solo los propios)

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| POST   | `/pedidos` | Finalizar compra: descuenta stock y vacía el carrito (409 si vacío/sin stock) |
| GET    | `/pedidos` | Mis pedidos |
| GET    | `/pedidos/{id}` | Uno de mis pedidos (404 si es de otro) |

### Administración

| Método | Ruta                      | Auth        | Descripción |
| ------ | ------------------------- | ----------- | ----------- |
| GET    | `/admin/pedidos`          | staff/owner | Pedidos de **todos** los clientes |
| GET    | `/admin/usuarios`         | owner       | Listar usuarios con su rol |
| PATCH  | `/admin/usuarios/{u}/rol` | owner       | Cambiar rol (`{"rol": "client\|staff\|owner"}`) |
| DELETE | `/admin/usuarios/{u}`     | owner       | Eliminar usuario (204) |

## Frontend (Vue 3)

SPA con estética neón / synthwave (**Pixel Vault**): fondo animado, tipografías
Orbitron + Rajdhani, tarjetas con glassmorphism, chips de plataforma con color
propio y microanimaciones. La navegación se hace con un **menú hamburguesa** en la
cabecera; cada sección es una "página" con su propia URL.

| Ruta               | Página               | Acceso            |
| ------------------ | -------------------- | ----------------- |
| `/tienda`          | Catálogo (+ filtros) | todos             |
| `/carrito`         | Carrito              | todos             |
| `/pedidos`         | Mis pedidos          | todos             |
| `/publicar`        | Publicar juego       | `staff` / `owner` |
| `/pedidos-tienda`  | Pedidos de la tienda | `staff` / `owner` |
| `/usuarios`        | Usuarios y roles     | `owner`           |
| `/acceso`          | Login / registro     | sin sesión        |

El menú solo muestra las secciones permitidas por el rol; si se escribe a mano una
ruta restringida, el router redirige a `/tienda`. Esto es solo UX: **el backend
valida el rol en cada petición**.

## Prueba de humo

Con el backend en marcha:

```bash
python smoke_test.py
```

**62 comprobaciones** que cubren: API pública, registro (y que nunca se devuelve la
contraseña), login y roles, **separación access/refresh**, **refresco con rotación y
detección de reuso**, logout, **CORS**, endpoints protegidos (401), **RBAC** completo
(403/404) y **aislamiento entre usuarios**. Usa `Authorization: Bearer`.

## Notas de diseño

- **Concurrencia:** el almacén usa un `threading.Lock` para evitar carreras entre
  peticiones simultáneas (p. ej. dos compras del mismo stock).
- **Validación:** Pydantic rechaza datos inválidos con `422`.
- **Persistencia:** al ser en memoria, basta con sustituir las funciones de
  `app/store.py` por llamadas a una base de datos manteniendo la misma interfaz.
- **Escalado a producción:** fija `SECRET_KEY`, usa HTTPS, restringe `CORS_ORIGINS`,
  sustituye el almacén en memoria por una base de datos y guarda los refresh tokens
  (y sus revocaciones) también en esa base de datos.
```