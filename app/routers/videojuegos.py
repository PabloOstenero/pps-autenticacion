"""Endpoints del catálogo de videojuegos.

La consulta del catálogo es pública. Crear y editar están reservados a `staff` y
`owner`; **eliminar** un juego (acción destructiva) solo lo puede hacer `owner`.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response, status

from .. import store
from ..security import SoloOwner, SoloStaff, UsuarioActual
from ..models import ErrorResponse, Videojuego, VideojuegoCreate, VideojuegoUpdate

router = APIRouter(prefix="/videojuegos", tags=["Videojuegos"])


@router.get("", response_model=list[Videojuego], summary="Listar videojuegos (público)")
def listar(
    plataforma: Optional[str] = Query(None, description="Filtrar por plataforma"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    buscar: Optional[str] = Query(None, min_length=1, description="Buscar por título o descripción"),
    disponibles: bool = Query(False, description="Solo con stock"),
    orden: str = Query("titulo", pattern="^(titulo|precio_asc|precio_desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    resultados = store.listar_videojuegos(
        plataforma=plataforma, categoria=categoria, buscar=buscar, disponibles=disponibles, orden=orden
    )
    return resultados[skip : skip + limit]


@router.get("/{videojuego_id}", response_model=Videojuego, responses={404: {"model": ErrorResponse}},
            summary="Obtener un videojuego (público)")
def obtener(videojuego_id: int):
    videojuego = store.obtener_videojuego(videojuego_id)
    if videojuego is None:
        raise HTTPException(status_code=404, detail=f"No existe el videojuego {videojuego_id}")
    return videojuego


@router.post("", response_model=Videojuego, status_code=status.HTTP_201_CREATED,
             responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
             summary="Crear videojuego (staff/owner)")
def crear(datos: VideojuegoCreate, usuario: SoloStaff):
    return store.crear_videojuego(datos)


@router.put("/{videojuego_id}", response_model=Videojuego,
            responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
            summary="Actualizar videojuego (staff/owner)")
def actualizar(videojuego_id: int, cambios: VideojuegoUpdate, usuario: SoloStaff):
    actualizado = store.actualizar_videojuego(videojuego_id, cambios)
    if actualizado is None:
        raise HTTPException(status_code=404, detail=f"No existe el videojuego {videojuego_id}")
    return actualizado


@router.delete("/{videojuego_id}", status_code=status.HTTP_204_NO_CONTENT,
               responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
               summary="Eliminar videojuego (solo owner)")
def eliminar(videojuego_id: int, usuario: SoloOwner):
    if not store.eliminar_videojuego(videojuego_id):
        raise HTTPException(status_code=404, detail=f"No existe el videojuego {videojuego_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
