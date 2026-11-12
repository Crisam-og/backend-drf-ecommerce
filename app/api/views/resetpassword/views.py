import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode

from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework.views import APIView
from api.models.user.ResetPassword import PasswordResetThrottle, PasswordResetConfirmThrottle, _puede_resetear, MENSAJE_SOLICITUD, MENSAJE_ENLACE_INVALIDO, logger
from api.serializers.password.serializer import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from api.models.user.models import UsuarioModel


def enviar_enlace_password(user, *, invitacion: bool = False) -> bool:
    """
    Envía por correo el enlace para definir la contraseña y devuelve True si
    el mensaje salió. Con invitacion=True el texto es de bienvenida (cuenta
    recién creada por un administrador).
    """
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    token = default_token_generator.make_token(user)
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/restablecer-password/{uid}/{token}"
    minutos = settings.PASSWORD_RESET_TIMEOUT // 60
    vigencia = f"{minutos // 60} hora(s)" if minutos >= 60 else f"{minutos} minutos"
    nombre = user.first_name or user.email
 
    if invitacion:
        asunto = "Te han creado una cuenta en el panel administrativo"
        mensaje = (
            f"Hola {nombre},\n\n"
            "Se creó una cuenta para ti en el panel administrativo.\n\n"
            f"Abre este enlace para definir tu contraseña "
            f"(vence en {vigencia} y solo se puede usar una vez):\n\n"
            f"{enlace}\n\n"
            "Si el enlace vence, entra al panel y usa «¿Olvidaste tu contraseña?» "
            "para recibir uno nuevo."
        )
    else:
        asunto = "Restablece tu contraseña"
        mensaje = (
            f"Hola {nombre},\n\n"
            "Recibimos una solicitud para restablecer la contraseña de tu cuenta "
            "del panel administrativo.\n\n"
            f"Abre este enlace para elegir una nueva contraseña "
            f"(vence en {vigencia} y solo se puede usar una vez):\n\n"
            f"{enlace}\n\n"
            "Si no hiciste esta solicitud, ignora este mensaje: tu contraseña "
            "seguirá siendo la misma."
        )
 
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            recipient_list=[user.email],
        )
        return True
    except Exception:
        logger.exception("No se pudo enviar el correo de contraseña")
        return False
        
class PasswordResetRequestView(APIView):
    """POST {"email"} -> envía el enlace si la cuenta existe y es de administrador."""
 
    # Sin autenticación: un token viejo o expirado en el header no debe
    # provocar un 401 en un endpoint pensado para quien no puede iniciar sesión
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]
 
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
 
        user = UsuarioModel.objects.filter(email__iexact=email).first()
 
        # cache.add devuelve False si la clave ya existe: evita que alguien use
        # este endpoint para llenar de correos la bandeja de otra persona
        cooldown = getattr(settings, "PASSWORD_RESET_COOLDOWN", 60)
        if user and _puede_resetear(user) and cache.add(f"pwreset:{email}", 1, cooldown):
            self._enviar_correo(user)
 
        return Response({"detail": MENSAJE_SOLICITUD})
 
    @staticmethod
    def _enviar_correo(user):
        # Si falla, la respuesta al cliente no cambia (el error ya queda registrado)
        enviar_enlace_password(user)
 
 
class PasswordResetValidateView(APIView):
    """
    POST {"uid", "token"} -> 200 si el enlace sigue siendo válido, 400 si no.
    No consume el token: solo permite que el frontend muestre el formulario
    únicamente cuando el enlace sirve.
    """
 
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetConfirmThrottle]
 
    def post(self, request):
        uid = str(request.data.get("uid", ""))
        token = str(request.data.get("token", ""))
 
        user = PasswordResetConfirmSerializer._obtener_usuario(uid)
        if (
            user is None
            or not _puede_resetear(user)
            or not default_token_generator.check_token(user, token)
        ):
            return Response({"detail": MENSAJE_ENLACE_INVALIDO}, status=400)
        return Response({"detail": "Enlace válido."})
 
 
class PasswordResetConfirmView(APIView):
    """POST {"uid", "token", "password", "password2"} -> cambia la contraseña."""
 
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetConfirmThrottle]
 
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contraseña actualizada. Ya puedes iniciar sesión."})

