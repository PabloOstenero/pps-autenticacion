"""Endpoints de registro, login, refresco de token y sesión.

Flujo de tokens
---------------
1. `POST /auth/registro` y `POST /auth/login` devuelven un par
   **access_token** (vida corta) + **refresh_token** (vida larga, con `jti`
   registrado en el servidor).
2. Cuando el access token caduca, el cliente llama a `POST /auth/refresh` con su
   refresh token. El servidor **rota** el refresh (invalida el antiguo y emite
   uno nuevo).
3. Si llega un refresh token ya rotado (posible robo), se **revocan todas** las
   sesiones de ese usuario y se responde 401.
4. `POST /auth/logout` revoca el refresh token presentado.
"""

from fastapi import APIRouter, HTTPException, status

from .. import security, store
from ..models import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    Usuario,
    UsuarioCrear,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

_invalido = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Usuario o contraseña incorrectos",
    headers={"WWW-Authenticate": "Bearer"},
)

_refresh_invalido = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Refresh token inválido o caducado",
    headers={"WWW-Authenticate": "Bearer"},
)


def _emitir_tokens(usuario: Usuario) -> TokenResponse:
    """Emite y registra un par de tokens para el usuario."""
    access, expira = security.crear_access_token(usuario.username, usuario.rol)
    refresh, jti, _ = security.crear_refresh_token(usuario.username)
    store.registrar_refresh(jti, usuario.username)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=expira,
        usuario=usuario,
    )


@router.post(
    "/registro",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario (entra como 'client' y queda autenticado)",
)
def registro(datos: UsuarioCrear):
    if store.obtener_usuario(datos.username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="El nombre de usuario ya está en uso")
    usuario = store.crear_usuario(datos.username, security.hashear_password(datos.password))
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="El nombre de usuario ya está en uso")
    return _emitir_tokens(usuario)


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(datos: LoginRequest):
    registro = store.obtener_registro_usuario(datos.username)
    if registro is None or not security.verificar_password(datos.password, registro.password_hash):
        raise _invalido
    return _emitir_tokens(registro.publico())


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"description": "Refresh token inválido, caducado o reutilizado"}},
    summary="Obtener un nuevo access token (rota el refresh token)",
)
def refresh(datos: RefreshRequest):
    payload = security.decodificar(datos.refresh_token, tipo_esperado="refresh")
    if payload is None:
        raise _refresh_invalido

    username = payload.get("sub", "")
    jti = payload.get("jti", "")
    usuario = store.obtener_usuario(username)
    if usuario is None:
        raise _refresh_invalido

    if store.consumir_refresh(jti):
        # Rotación normal: el refresh usado deja de valer y se emite otro.
        return _emitir_tokens(usuario)

    # El token está bien firmado pero ya no está activo. Si lo conocemos, es un
    # reuso de un token rotado -> posible robo: cerramos todas las sesiones.
    if store.refresco_es_conocido(jti):
        store.revocar_todos_los_refrescos(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reutilizado: se han revocado todas las sesiones por seguridad",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise _refresh_invalido


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
def logout(datos: LogoutRequest | None = None):
    """Revoca el refresh token presentado (si lo hay)."""
    if datos and datos.refresh_token:
        # Aunque esté caducado, nos interesa su jti para revocarlo.
        payload = security.decodificar(datos.refresh_token, tipo_esperado="refresh", verificar_exp=False)
        if payload:
            store.revocar_refresh(payload.get("jti", ""))
    return None


@router.post("/logout-todo", status_code=status.HTTP_204_NO_CONTENT,
             summary="Cerrar todas mis sesiones")
def logout_todo(usuario: security.UsuarioActual):
    store.revocar_todos_los_refrescos(usuario.username)
    return None


@router.get("/me", response_model=Usuario, summary="Usuario autenticado")
def me(usuario: security.UsuarioActual):
    return usuario
