
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from api.models.user.models import UsuarioModel
from api.models.user.ResetPassword import _puede_resetear, MENSAJE_ENLACE_INVALIDO
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

# ---------------------------------------------------------------------------
# Cambio de contraseña (sirve para cliente y administrador)
# ---------------------------------------------------------------------------
class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True)
    password_nueva2 = serializers.CharField(write_only=True)
 
    def validate_password_actual(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value
 
    def validate(self, attrs):
        if attrs["password_nueva"] != attrs["password_nueva2"]:
            raise serializers.ValidationError(
                {"password_nueva2": "Las contraseñas no coinciden."}
            )
        if attrs["password_nueva"] == attrs["password_actual"]:
            raise serializers.ValidationError(
                {"password_nueva": "La nueva contraseña debe ser distinta a la actual."}
            )
        try:
            validate_password(attrs["password_nueva"], user=self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password_nueva": list(exc.messages)})
        return attrs
 
    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["password_nueva"])
        user.save(update_fields=["password"])
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
 
 
class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
 
    @staticmethod
    def _obtener_usuario(uid):
        try:
            pk = force_str(urlsafe_base64_decode(uid))
            return UsuarioModel.objects.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            DjangoValidationError,  # UUID mal formado
            UsuarioModel.DoesNotExist,
        ):
            return None
 
    def validate(self, attrs):
        user = self._obtener_usuario(attrs["uid"])
 
        # Un único mensaje para uid inválido, token inválido, token vencido
        # o usuario no permitido: no da pistas a quien tantea enlaces
        if (
            user is None
            or not _puede_resetear(user)
            or not default_token_generator.check_token(user, attrs["token"])
        ):
            raise serializers.ValidationError({"token": [MENSAJE_ENLACE_INVALIDO]})
 
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password2": ["Las contraseñas no coinciden."]}
            )
 
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
 
        attrs["user"] = user
        return attrs
 
    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password"])
 
        # Cierra todas las sesiones abiertas: invalida los refresh tokens vigentes
        for outstanding in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding)
        return user