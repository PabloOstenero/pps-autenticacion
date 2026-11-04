"""Endpoints de gestión de la tienda (panel de administración).

- `staff` (empleado) y `owner` (dueño) pueden consultar los pedidos de **todos**
  los clientes para prepararlos. Un `client` nunca ve pedidos ajenos.
- Solo `owner` puede listar usuarios, cambiarles el rol o eliminarlos.
"""

from fastapi import APIRouter, HTTPException, status

from .. import store
from ..security import SoloOwner, SoloStaff
from ..models import ErrorResponse, Pedido, Usuario, UsuarioRolUpdate

router = APIRouter(prefix="/admin", tags=["Administración"])


def _propietarios() -> list[Usuario]:
    """Dueños actuales de la tienda (para no quedarnos sin ninguno)."""
    return [u for u in store.listar_usuarios() if u.rol == "owner"]


@router.get("/usuarios", response_model=list[Usuario], summary="Listar usuarios (owner)")
def listar_usuarios(owner: SoloOwner):
    return store.listar_usuarios()


@router.patch(
    "/usuarios/{username}/rol",
    response_model=Usuario,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse},
               404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Cambiar el rol de un usuario (owner)",
)
def cambiar_rol(username: str, datos: UsuarioRolUpdate, owner: SoloOwner):
    registro = store.obtener_usuario(username)
    if registro is None:
        raise HTTPException(status_code=404, detail=f"No existe el usuario «{username}»")
    if username.strip().lower() == owner.username.lower() and datos.rol != "owner":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No puedes retirarte a ti mismo el rol de dueño")
    if registro.rol == "owner" and datos.rol != "owner" and len(_propietarios()) <= 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="La tienda no puede quedarse sin ningún dueño")
    return store.cambiar_rol(username, datos.rol)


@router.delete(
    "/usuarios/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse},
               404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Eliminar un usuario (owner)",
)
def eliminar_usuario(username: str, owner: SoloOwner):
    registro = store.obtener_usuario(username)
    if registro is None:
        raise HTTPException(status_code=404, detail=f"No existe el usuario «{username}»")
    if username.strip().lower() == owner.username.lower():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No puedes eliminar tu propia cuenta")
    if registro.rol == "owner" and len(_propietarios()) <= 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="La tienda no puede quedarse sin ningún dueño")
    store.eliminar_usuario(username)
    return None


@router.get("/pedidos", response_model=list[Pedido],
            summary="Pedidos de todos los clientes (staff/owner)")
def listar_todos_los_pedidos(usuario: SoloStaff):
    return store.listar_todos_los_pedidos()
