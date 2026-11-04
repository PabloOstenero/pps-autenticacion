"""Autenticación con JWT (access + refresh) y hash de contraseñas (bcrypt).

Diseño de tokens
----------------
- **Access token**: JWT de vida corta (15 min por defecto). Es el que se envía en
  `Authorization: Bearer <token>` en cada petición a la API.
- **Refresh token**: JWT de vida larga (7 días por defecto) que SOLO sirve para
  pedir un nuevo access token en `POST /auth/refresh`. Lleva un `jti` (id único)
  registrado en el servidor, de modo que se puede **rotar** y **revocar**.

El campo `tipo` ("access"/"refresh") del payload impide que un refresh token
valga como access token y viceversa.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status

from . import store
from .models import Usuario

# En producción define SECRET_KEY por variable de entorno: sin ella, los
# tokens se podrían falsificar. Se genera una aleatoria como último recurso.
SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

_credenciales_invalidas = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado o token inválido",
    headers={"WWW-Authenticate": "Bearer"},
)


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Emisión de tokens
# --------------------------------------------------------------------------- #

def _codificar(sub: str, tipo: str, expira: timedelta, jti: Optional[str] = None,
              extras: Optional[dict] = None) -> tuple[str, str]:
    """Firma un JWT. Devuelve (token, jti)."""
    ahora = datetime.now(timezone.utc)
    jti = jti or uuid.uuid4().hex
    payload = {"sub": sub, "tipo": tipo, "jti": jti, "iat": ahora, "exp": ahora + expira}
    if extras:
        payload.update(extras)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), jti


def crear_access_token(username: str, rol: str) -> tuple[str, int]:
    """Devuelve (access_token, segundos_de_validez)."""
    expira = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token, _ = _codificar(username, "access", expira, extras={"rol": rol})
    return token, int(expira.total_seconds())


def crear_refresh_token(username: str) -> tuple[str, str, int]:
    """Devuelve (refresh_token, jti, segundos_de_validez). El jti debe registrarse."""
    expira = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token, jti = _codificar(username, "refresh", expira)
    return token, jti, int(expira.total_seconds())


def decodificar(token: str, tipo_esperado: str = "access", verificar_exp: bool = True) -> Optional[dict]:
    """Valida firma y tipo. Devuelve el payload o None si no es válido."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": verificar_exp},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("tipo") != tipo_esperado:
        return None
    return payload


# --------------------------------------------------------------------------- #
# Dependencias de FastAPI
# --------------------------------------------------------------------------- #

def _token_de_peticion(request: Request) -> Optional[str]:
    """El token viaja en la cabecera `Authorization: Bearer <token>`."""
    cabecera = request.headers.get("Authorization", "")
    if cabecera.lower().startswith("bearer "):
        return cabecera[7:].strip()
    return None


def usuario_actual(request: Request) -> Usuario:
    token = _token_de_peticion(request)
    if not token:
        raise _credenciales_invalidas
    payload = decodificar(token, "access")
    if payload is None:
        raise _credenciales_invalidas
    usuario = store.obtener_usuario(payload.get("sub", ""))
    if usuario is None:
        raise _credenciales_invalidas
    return usuario


# Dependencia reutilizable en los routers.
UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


def requiere_roles(*roles: str):
    """Exige que el usuario tenga uno de esos roles (RBAC).

    El rol se comprueba contra el almacén (no contra el token), de modo que un
    cambio de rol tiene efecto inmediato aunque el token siga siendo válido.
    """

    def dependencia(usuario: UsuarioActual) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acción reservada a: {', '.join(roles)}. Tu rol es «{usuario.rol}».",
            )
        return usuario

    return dependencia


# Atajos listos para usar en los routers:
#   - client: cliente final. Solo compra (carrito y pedidos propios).
#   - staff:  empleado; gestiona el catálogo y ve los pedidos de la tienda.
#   - owner:  dueño; además administra usuarios y roles.
SoloStaff = Annotated[Usuario, Depends(requiere_roles("owner", "staff"))]
SoloOwner = Annotated[Usuario, Depends(requiere_roles("owner"))]
