"""Endpoints del carrito de la compra (requieren sesión)."""

from fastapi import APIRouter, HTTPException, Query, status

from .. import store
from ..security import UsuarioActual
from ..models import Carrito, ErrorResponse, ItemCarrito

router = APIRouter(prefix="/carrito", tags=["Carrito"])


def _resumen(items: list[ItemCarrito]) -> Carrito:
    return Carrito(
        items=items,
        total=round(sum(i.subtotal for i in items), 2),
        num_articulos=sum(i.cantidad for i in items),
    )


def _error_item(motivo: str, videojuego_id: int) -> HTTPException:
    if motivo == "no_existe":
        return HTTPException(status_code=404, detail=f"No existe el videojuego {videojuego_id}")
    if motivo == "no_en_carrito":
        return HTTPException(status_code=404, detail=f"El videojuego {videojuego_id} no está en el carrito")
    return HTTPException(status_code=409, detail="No hay stock suficiente para esa cantidad")


@router.get("", response_model=Carrito, responses={401: {"model": ErrorResponse}}, summary="Ver mi carrito")
def ver_carrito(usuario: UsuarioActual):
    return _resumen(store.obtener_carrito(usuario.username))


@router.post(
    "",
    response_model=Carrito,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Añadir un videojuego a mi carrito",
)
def anadir(usuario: UsuarioActual, videojuego_id: int = Query(..., description="Id del videojuego"),
           cantidad: int = Query(1, ge=1, le=99)):
    _, motivo = store.anadir_al_carrito(usuario.username, videojuego_id, cantidad)
    if motivo:
        raise _error_item(motivo, videojuego_id)
    return _resumen(store.obtener_carrito(usuario.username))


@router.patch(
    "/{videojuego_id}",
    response_model=Carrito,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Cambiar la cantidad de un artículo (0 lo elimina)",
)
def cambiar_cantidad(usuario: UsuarioActual, videojuego_id: int, cantidad: int = Query(..., ge=0, le=99)):
    _, motivo = store.actualizar_item_carrito(usuario.username, videojuego_id, cantidad)
    if motivo:
        raise _error_item(motivo, videojuego_id)
    return _resumen(store.obtener_carrito(usuario.username))


@router.delete(
    "/{videojuego_id}",
    response_model=Carrito,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Quitar un videojuego de mi carrito",
)
def quitar(usuario: UsuarioActual, videojuego_id: int):
    if not store.eliminar_del_carrito(usuario.username, videojuego_id):
        raise _error_item("no_en_carrito", videojuego_id)
    return _resumen(store.obtener_carrito(usuario.username))


@router.delete("", response_model=Carrito, responses={401: {"model": ErrorResponse}},
               summary="Vaciar mi carrito")
def vaciar(usuario: UsuarioActual):
    store.vaciar_carrito(usuario.username)
    return _resumen([])
