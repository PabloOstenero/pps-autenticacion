"""Endpoints de pedidos (requieren sesión y son privados por usuario)."""

from fastapi import APIRouter, HTTPException, status

from .. import store
from ..security import UsuarioActual
from ..models import ErrorResponse, Pedido

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("", response_model=list[Pedido], responses={401: {"model": ErrorResponse}},
            summary="Listar mis pedidos")
def listar(usuario: UsuarioActual):
    return store.listar_pedidos(usuario.username)


@router.get("/{pedido_id}", response_model=Pedido,
            responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
            summary="Obtener uno de mis pedidos")
def obtener(pedido_id: int, usuario: UsuarioActual):
    pedido = store.obtener_pedido(usuario.username, pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail=f"No existe el pedido {pedido_id}")
    return pedido


@router.post(
    "",
    response_model=Pedido,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Finalizar la compra de mi carrito",
)
def crear(usuario: UsuarioActual):
    pedido, motivo = store.crear_pedido(usuario.username)
    if motivo == "carrito_vacio":
        raise HTTPException(status_code=409, detail="El carrito está vacío")
    if motivo and motivo.startswith("sin_stock:"):
        titulo = motivo.split(":", 1)[1]
        raise HTTPException(status_code=409, detail=f"Stock insuficiente de «{titulo}»")
    return pedido
