"""Esquemas Pydantic de la tienda de videojuegos."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Plataforma = Literal["PC", "PS5", "Xbox Series", "Switch", "Multiplataforma"]

# Roles de la tienda:
#   - owner  (dueño):      control total, administra el personal y el catálogo.
#   - staff  (empleado):   gestiona el catálogo y prepara los pedidos.
#   - client (cliente):    compra; solo ve su carrito y sus pedidos.
Rol = Literal["owner", "staff", "client"]


# --------------------------------------------------------------------------- #
# Videojuegos
# --------------------------------------------------------------------------- #

class VideojuegoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150, examples=["Hollow Knight"])
    plataforma: Plataforma = "Multiplataforma"
    categoria: str = Field(..., min_length=1, max_length=50, examples=["Metroidvania"])
    precio: float = Field(..., ge=0, examples=[19.99])
    stock: int = Field(0, ge=0, examples=[10])
    descripcion: Optional[str] = Field(None, max_length=1000)
    fecha_lanzamiento: Optional[date] = None


class VideojuegoCreate(VideojuegoBase):
    pass


class VideojuegoUpdate(BaseModel):
    """Campos opcionales: solo se actualizan los enviados."""

    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    plataforma: Optional[Plataforma] = None
    categoria: Optional[str] = Field(None, min_length=1, max_length=50)
    precio: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    descripcion: Optional[str] = Field(None, max_length=1000)
    fecha_lanzamiento: Optional[date] = None


class Videojuego(VideojuegoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --------------------------------------------------------------------------- #
# Carrito
# --------------------------------------------------------------------------- #

class ItemCarrito(BaseModel):
    videojuego_id: int
    titulo: str
    precio_unitario: float
    cantidad: int = Field(..., ge=1)
    subtotal: float


class Carrito(BaseModel):
    items: list[ItemCarrito]
    total: float
    num_articulos: int


# --------------------------------------------------------------------------- #
# Pedidos
# --------------------------------------------------------------------------- #

class ItemPedido(BaseModel):
    videojuego_id: int
    titulo: str
    precio_unitario: float
    cantidad: int
    subtotal: float


class Pedido(BaseModel):
    id: int
    usuario: str
    items: list[ItemPedido]
    total: float
    num_articulos: int
    fecha: datetime
    estado: Literal["pendiente", "enviado", "entregado"] = "pendiente"


# --------------------------------------------------------------------------- #
# Usuarios y autenticación
# --------------------------------------------------------------------------- #

class UsuarioCrear(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$",
                          examples=["jugador1"])
    password: str = Field(..., min_length=8, max_length=72, examples=["contraseña-segura"])


class Usuario(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    rol: Rol
    creado: datetime


class UsuarioRolUpdate(BaseModel):
    rol: Rol


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, examples=["jugador1"])
    password: str = Field(..., min_length=1, max_length=72, examples=["contraseña-segura"])



class TokenResponse(BaseModel):
    """Par de tokens que devuelve el login/registro/refresh.

    - `access_token`: se usa en `Authorization: Bearer` en cada petición.
    - `refresh_token`: solo sirve para pedir un nuevo access token en
      `/auth/refresh` (se rota en cada uso).
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: Usuario


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class ErrorResponse(BaseModel):
    detalle: str
