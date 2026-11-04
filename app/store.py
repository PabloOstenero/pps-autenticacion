"""Almacén en memoria de la tienda.

Todo se pierde al reiniciar el servidor: suficiente para pruebas y desarrollos
tempranos. Si más adelante se necesita persistencia, basta con sustituir estas
estructuras por una base de datos manteniendo la misma interfaz.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from itertools import count
from threading import Lock
from typing import Optional

from .models import (
    ItemCarrito,
    ItemPedido,
    Pedido,
    Usuario,
    Videojuego,
    VideojuegoCreate,
    VideojuegoUpdate,
)


@dataclass
class _RegistroUsuario:
    """Usuario tal y como se guarda internamente (con el hash de la contraseña)."""

    username: str
    password_hash: str
    rol: str
    creado: datetime

    def publico(self) -> Usuario:
        return Usuario(username=self.username, rol=self.rol, creado=self.creado)


# Catálogo: id -> Videojuego
_videojuegos: dict[int, Videojuego] = {}
# Usuarios: username en minúsculas -> registro
_usuarios: dict[str, _RegistroUsuario] = {}
# Carritos: username en minúsculas -> {videojuego_id: ItemCarrito}
_carritos: dict[str, dict[int, ItemCarrito]] = {}
# Pedidos: id -> Pedido
_pedidos: dict[int, Pedido] = {}

_videojuego_ids = count(1)
_pedido_ids = count(1)

# El servidor puede atender varias peticiones en paralelo: protegemos los
# accesos para evitar condiciones de carrera (p. ej. dos compras del mismo stock).
lock = Lock()


def _clave(username: str) -> str:
    return username.strip().lower()


def _carrito_de(usuario: str) -> dict[int, ItemCarrito]:
    return _carritos.setdefault(_clave(usuario), {})


def semilla() -> None:
    """Carga algunos videojuegos de ejemplo si el catálogo está vacío."""
    if _videojuegos:
        return
    ejemplos = [
        VideojuegoCreate(titulo="Hollow Knight", plataforma="Multiplataforma", categoria="Metroidvania",
                         precio=14.99, stock=25, descripcion="Explora un reino en ruinas lleno de insectos y secretos.",
                         fecha_lanzamiento=date(2017, 2, 24)),
        VideojuegoCreate(titulo="Elden Ring", plataforma="PC", categoria="RPG de acción",
                         precio=59.99, stock=12, descripcion="Un mundo abierto oscuro y desafiante.",
                         fecha_lanzamiento=date(2022, 2, 25)),
        VideojuegoCreate(titulo="The Legend of Zelda: Tears of the Kingdom", plataforma="Switch",
                         categoria="Aventura", precio=69.99, stock=8,
                         descripcion="Construye, explora y sobrevive en Hyrule.", fecha_lanzamiento=date(2023, 5, 12)),
        VideojuegoCreate(titulo="Forza Horizon 5", plataforma="Xbox Series", categoria="Carreras",
                         precio=49.99, stock=15, descripcion="Carrera arcade por México.", fecha_lanzamiento=date(2021, 11, 9)),
        VideojuegoCreate(titulo="Celeste", plataforma="PC", categoria="Plataformas",
                         precio=9.99, stock=30, descripcion="Sube la montaña, supera tus límites.", fecha_lanzamiento=date(2018, 1, 25)),
    ]
    for ejemplo in ejemplos:
        crear_videojuego(ejemplo)


# --------------------------------------------------------------------------- #
# Usuarios
# --------------------------------------------------------------------------- #

def crear_usuario(username: str, password_hash: str, rol: str = "client") -> Optional[Usuario]:
    """Crea un usuario. Devuelve None si el nombre ya está en uso."""
    with lock:
        clave = _clave(username)
        if clave in _usuarios:
            return None
        registro = _RegistroUsuario(username=username.strip(), password_hash=password_hash,
                                    rol=rol, creado=datetime.now(timezone.utc))
        _usuarios[clave] = registro
        return registro.publico()


def obtener_registro_usuario(username: str) -> Optional[_RegistroUsuario]:
    with lock:
        return _usuarios.get(_clave(username))


def obtener_usuario(username: str) -> Optional[Usuario]:
    registro = obtener_registro_usuario(username)
    return registro.publico() if registro else None


def listar_usuarios() -> list[Usuario]:
    with lock:
        return sorted((r.publico() for r in _usuarios.values()), key=lambda u: u.username.lower())


def cambiar_rol(username: str, rol: str) -> Optional[Usuario]:
    """Cambia el rol de un usuario. Devuelve None si no existe."""
    with lock:
        registro = _usuarios.get(_clave(username))
        if registro is None:
            return None
        registro.rol = rol
        return registro.publico()


def eliminar_usuario(username: str) -> bool:
    with lock:
        clave = _clave(username)
        if clave not in _usuarios:
            return False
        del _usuarios[clave]
        # Limpiamos también su carrito y sus refresh tokens.
        _carritos.pop(clave, None)
        for jti in [j for j, u in _refrescos_activos.items() if u == clave]:
            del _refrescos_activos[jti]
        return True


# --------------------------------------------------------------------------- #
# Videojuegos
# --------------------------------------------------------------------------- #

def listar_videojuegos(
    plataforma: Optional[str] = None,
    categoria: Optional[str] = None,
    buscar: Optional[str] = None,
    disponibles: bool = False,
    orden: str = "titulo",
) -> list[Videojuego]:
    with lock:
        resultados = list(_videojuegos.values())

    if plataforma:
        resultados = [v for v in resultados if v.plataforma == plataforma]
    if categoria:
        resultados = [v for v in resultados if v.categoria.lower() == categoria.lower()]
    if buscar:
        texto = buscar.lower()
        resultados = [v for v in resultados if texto in v.titulo.lower() or texto in (v.descripcion or "").lower()]
    if disponibles:
        resultados = [v for v in resultados if v.stock > 0]

    if orden == "precio_asc":
        resultados.sort(key=lambda v: v.precio)
    elif orden == "precio_desc":
        resultados.sort(key=lambda v: -v.precio)
    else:
        resultados.sort(key=lambda v: v.titulo.lower())
    return resultados


def obtener_videojuego(videojuego_id: int) -> Optional[Videojuego]:
    with lock:
        return _videojuegos.get(videojuego_id)


def crear_videojuego(datos: VideojuegoCreate) -> Videojuego:
    with lock:
        videojuego = Videojuego(id=next(_videojuego_ids), **datos.model_dump())
        _videojuegos[videojuego.id] = videojuego
        return videojuego


def actualizar_videojuego(videojuego_id: int, cambios: VideojuegoUpdate) -> Optional[Videojuego]:
    with lock:
        videojuego = _videojuegos.get(videojuego_id)
        if videojuego is None:
            return None
        actualizado = videojuego.model_copy(update=cambios.model_dump(exclude_unset=True))
        _videojuegos[videojuego_id] = actualizado
        return actualizado


def eliminar_videojuego(videojuego_id: int) -> bool:
    with lock:
        if videojuego_id not in _videojuegos:
            return False
        del _videojuegos[videojuego_id]
        # Fuera del catálogo, fuera de todos los carritos.
        for carrito in _carritos.values():
            carrito.pop(videojuego_id, None)
        return True


# --------------------------------------------------------------------------- #
# Carrito (por usuario)
# --------------------------------------------------------------------------- #

def obtener_carrito(usuario: str) -> list[ItemCarrito]:
    with lock:
        return sorted(_carrito_de(usuario).values(), key=lambda i: i.titulo.lower())


def anadir_al_carrito(usuario: str, videojuego_id: int, cantidad: int) -> tuple[Optional[ItemCarrito], Optional[str]]:
    """Añade (o incrementa) un artículo. Devuelve (item, motivo_error)."""
    with lock:
        videojuego = _videojuegos.get(videojuego_id)
        if videojuego is None:
            return None, "no_existe"
        carrito = _carrito_de(usuario)
        existente = carrito.get(videojuego_id)
        cantidad_final = cantidad + (existente.cantidad if existente else 0)
        if cantidad_final > videojuego.stock:
            return None, "sin_stock"
        item = ItemCarrito(
            videojuego_id=videojuego_id,
            titulo=videojuego.titulo,
            precio_unitario=videojuego.precio,
            cantidad=cantidad_final,
            subtotal=round(videojuego.precio * cantidad_final, 2),
        )
        carrito[videojuego_id] = item
        return item, None


def actualizar_item_carrito(usuario: str, videojuego_id: int, cantidad: int) -> tuple[Optional[ItemCarrito], Optional[str]]:
    """Cambia la cantidad de un artículo; 0 lo elimina."""
    with lock:
        carrito = _carrito_de(usuario)
        if videojuego_id not in carrito:
            return None, "no_en_carrito"
        if cantidad == 0:
            del carrito[videojuego_id]
            return None, None
        videojuego = _videojuegos.get(videojuego_id)
        if videojuego is None:
            del carrito[videojuego_id]
            return None, "no_existe"
        if cantidad > videojuego.stock:
            return None, "sin_stock"
        item = ItemCarrito(
            videojuego_id=videojuego_id,
            titulo=videojuego.titulo,
            precio_unitario=videojuego.precio,
            cantidad=cantidad,
            subtotal=round(videojuego.precio * cantidad, 2),
        )
        carrito[videojuego_id] = item
        return item, None


def eliminar_del_carrito(usuario: str, videojuego_id: int) -> bool:
    with lock:
        return _carrito_de(usuario).pop(videojuego_id, None) is not None


def vaciar_carrito(usuario: str) -> None:
    with lock:
        _carrito_de(usuario).clear()


# --------------------------------------------------------------------------- #
# Pedidos (por usuario)
# --------------------------------------------------------------------------- #

def crear_pedido(usuario: str) -> tuple[Optional[Pedido], Optional[str]]:
    """Cobra el carrito del usuario: descuenta stock y lo vacía. Devuelve (pedido, motivo_error)."""
    with lock:
        carrito = _carrito_de(usuario)
        if not carrito:
            return None, "carrito_vacio"

        # Revalidamos el stock justo antes de comprar.
        for item in carrito.values():
            videojuego = _videojuegos.get(item.videojuego_id)
            if videojuego is None:
                return None, f"sin_stock:{item.titulo}"
            if item.cantidad > videojuego.stock:
                return None, f"sin_stock:{videojuego.titulo}"

        items: list[ItemPedido] = []
        for item in carrito.values():
            videojuego = _videojuegos[item.videojuego_id]
            videojuego.stock -= item.cantidad
            items.append(
                ItemPedido(
                    videojuego_id=item.videojuego_id,
                    titulo=item.titulo,
                    precio_unitario=item.precio_unitario,
                    cantidad=item.cantidad,
                    subtotal=item.subtotal,
                )
            )

        total = round(sum(i.subtotal for i in items), 2)
        pedido = Pedido(
            id=next(_pedido_ids),
            usuario=usuario,
            items=items,
            total=total,
            num_articulos=sum(i.cantidad for i in items),
            fecha=datetime.now(timezone.utc),
        )
        _pedidos[pedido.id] = pedido
        carrito.clear()
        return pedido, None


def listar_pedidos(usuario: str) -> list[Pedido]:
    with lock:
        propios = [p for p in _pedidos.values() if _clave(p.usuario) == _clave(usuario)]
        return sorted(propios, key=lambda p: p.id, reverse=True)


def listar_todos_los_pedidos() -> list[Pedido]:
    """Solo para administradores: pedidos de todos los usuarios."""
    with lock:
        return sorted(_pedidos.values(), key=lambda p: p.id, reverse=True)


def obtener_pedido(usuario: str, pedido_id: int) -> Optional[Pedido]:
    with lock:
        pedido = _pedidos.get(pedido_id)
        if pedido is None or _clave(pedido.usuario) != _clave(usuario):
            return None
        return pedido


# --------------------------------------------------------------------------- #
# Refresh tokens (rotación, revocación y detección de reuso)
# --------------------------------------------------------------------------- #

# jti -> username (normalizado): refresh tokens actualmente válidos.
_refrescos_activos: dict[str, str] = {}
# jti emitidos alguna vez: sirve para detectar el REUSO de un token ya rotado.
_refrescos_vistos: set[str] = set()


def registrar_refresh(jti: str, username: str) -> None:
    with lock:
        _refrescos_activos[jti] = _clave(username)
        _refrescos_vistos.add(jti)


def refresco_es_activo(jti: str, username: str) -> bool:
    with lock:
        return _refrescos_activos.get(jti) == _clave(username)


def refresco_es_conocido(jti: str) -> bool:
    """True si el jti se emitió alguna vez (aunque ya se haya rotado)."""
    with lock:
        return jti in _refrescos_vistos


def consumir_refresh(jti: str) -> bool:
    """Marca el jti como usado (rotación). True si seguía activo."""
    with lock:
        return _refrescos_activos.pop(jti, None) is not None


def revocar_refresh(jti: str) -> None:
    with lock:
        _refrescos_activos.pop(jti, None)


def revocar_todos_los_refrescos(username: str) -> int:
    """Invalida todas las sesiones (refresh tokens) de un usuario."""
    with lock:
        clave = _clave(username)
        caducados = [j for j, u in _refrescos_activos.items() if u == clave]
        for jti in caducados:
            del _refrescos_activos[jti]
        return len(caducados)
