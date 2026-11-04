"""API REST de una tienda de videojuegos (FastAPI) con autenticación JWT.

Arquitectura **distribuida**: este backend solo expone la API JSON; el frontend
(Vue 3 + Vite) vive en su propio proyecto y consume la API por HTTP (CORS).
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import security, store
from .routers import admin, auth, carrito, pedidos, videojuegos

# Orígenes permitidos para el frontend (separado). Configúralos por entorno.
CORS_ORIGINS = [
    origen.strip()
    for origen in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origen.strip()
]

# Usuarios de demostración (usuario / contraseña / rol).
USUARIOS_DEMO = [
    ("owner", "owner1234", "owner"),     # dueño de la tienda (administrador)
    ("staff", "staff1234", "staff"),     # empleado (gestor)
    ("client", "client1234", "client"),  # cliente
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.semilla()  # catálogo de ejemplo
    for username, password, rol in USUARIOS_DEMO:
        if store.obtener_usuario(username) is None:
            store.crear_usuario(username, security.hashear_password(password), rol)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="API Tienda de Videojuegos",
    description=(
        "API REST con autenticación **JWT** (access + refresh con rotación). "
        "CRUD del catálogo, carrito, pedidos y administración por **roles** "
        "(`owner`, `staff`, `client`). Los datos se guardan **en memoria**: se "
        "pierden al reiniciar el servidor."
    ),
    version="3.0.0",
)

# CORS: el frontend (Vue) corre en otro origen (p. ej. http://localhost:5173).
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(videojuegos.router)
app.include_router(carrito.router)
app.include_router(pedidos.router)
app.include_router(admin.router)


@app.get("/", include_in_schema=False, summary="Información de la API")
def raiz():
    return {
        "api": "Tienda de Videojuegos",
        "docs": "/docs",
        "salud": "/salud",
        "autenticacion": "JWT (Authorization: Bearer <access_token>)",
        "frontend": "Vue 3 + Vite (proyecto aparte, ver carpeta frontend/)",
    }


@app.get("/salud", tags=["Sistema"], summary="Comprobación de estado")
def salud():
    return {"estado": "ok"}
