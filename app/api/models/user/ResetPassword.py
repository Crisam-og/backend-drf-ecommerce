import logging
from rest_framework.throttling import AnonRateThrottle
from .models import UsuarioModel

logger = logging.getLogger(__name__)
 
# Misma respuesta exista o no el correo: no revela qué cuentas están registradas
MENSAJE_SOLICITUD = (
    "Si el correo está registrado, recibirás un enlace para restablecer "
    "tu contraseña."
)
MENSAJE_ENLACE_INVALIDO = "El enlace no es válido o ha expirado."
 
 
def _puede_resetear(user) -> bool:
    """Este flujo es solo para el panel administrativo."""
    return (
        user.is_active
        and user.is_staff
        and user.tipo_usuario == UsuarioModel.TipoUsuario.ADMIN
    )

# ---------------------------------------------------------------------------
# Throttles (se configuran en REST_FRAMEWORK -> DEFAULT_THROTTLE_RATES)
# ---------------------------------------------------------------------------
class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"
 
 
class PasswordResetConfirmThrottle(AnonRateThrottle):
    scope = "password_reset_confirm"