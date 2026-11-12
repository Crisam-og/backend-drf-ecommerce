from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from api.models.user.models import UsuarioModel
from api.models.user.BasePermission import EsAdministrador  # ajusta la ruta a donde la definiste


def datos_usuario(user):
    """Datos que el frontend necesita para armar la sesión."""
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "tipo_usuario": user.tipo_usuario,
        "is_superuser": user.is_superuser,
        # Formato "app_label.codename", p. ej. "tuapp.add_producto"
        "permisos": sorted(user.get_all_permissions()),
    }


# ---------------------------------------------------------------------------
# Serializers de login
# ---------------------------------------------------------------------------
class BaseLoginSerializer(TokenObtainPairSerializer):
    """
    Como USERNAME_FIELD = 'email', el body del login es {"email", "password"}.
    simplejwt ya rechaza credenciales incorrectas y usuarios inactivos.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["tipo_usuario"] = user.tipo_usuario
        return token

    def usuario_permitido(self, user) -> bool:
        raise NotImplementedError

    def validate(self, attrs):
        data = super().validate(attrs)  # autentica y deja el usuario en self.user

        # Mismo mensaje que credenciales incorrectas: no revela si el correo existe
        if not self.usuario_permitido(self.user):
            raise AuthenticationFailed("Credenciales inválidas.")

        data["user"] = datos_usuario(self.user)
        return data


class AdminLoginSerializer(BaseLoginSerializer):
    def usuario_permitido(self, user):
        return user.is_staff and user.tipo_usuario == UsuarioModel.TipoUsuario.ADMIN


class ClienteLoginSerializer(BaseLoginSerializer):
    def usuario_permitido(self, user):
        return user.tipo_usuario == UsuarioModel.TipoUsuario.CLIENTE


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------
class LoginThrottle(AnonRateThrottle):
    scope = "login"  # se configura en REST_FRAMEWORK -> DEFAULT_THROTTLE_RATES


class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminLoginSerializer
    throttle_classes = [LoginThrottle]


class ClienteLoginView(TokenObtainPairView):
    serializer_class = ClienteLoginSerializer
    throttle_classes = [LoginThrottle]


class LogoutView(APIView):
    """
    Invalida el refresh token. No exige access token: para invalidar un
    refresh hay que poseerlo, y así el logout funciona aunque el access
    ya haya expirado.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "Se requiere el refresh token."}, status=400)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            pass  # ya estaba expirado o invalidado: el objetivo se cumple igual
        return Response(status=204)


class AdminMeView(APIView):
    """Permite al frontend restaurar la sesión al recargar la página."""

    permission_classes = [IsAuthenticated, EsAdministrador]

    def get(self, request):
        return Response(datos_usuario(request.user))