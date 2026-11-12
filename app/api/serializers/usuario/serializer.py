import re
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from api.views.resetpassword.views import enviar_enlace_password
from api.models.user.models import AdministradorModel, ClienteUsuarioModel, UsuarioModel
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class BaseRegistroSerializer(serializers.ModelSerializer):
    """Campos y validaciones comunes a cliente y administrador."""
 
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
 
    class Meta:
        model = UsuarioModel
        fields = (
            "user_id",
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
        )
        read_only_fields = ("user_id",)
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }
 
    def validate_email(self, value):
        value = UsuarioModel.objects.normalize_email(value).lower()
        if UsuarioModel.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return value
 
    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password2": "Las contraseñas no coinciden."}
            )
 
        # Usuario temporal para que el validador de similitud compare con email/nombre
        usuario_temporal = UsuarioModel(
            email=attrs.get("email"),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], user=usuario_temporal)
        except Exception as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
 
        attrs.pop("password2")
        return attrs
 
 
class ClienteRegistroSerializer(BaseRegistroSerializer):
    direccion = serializers.CharField(max_length=150, write_only=True)
    telefono = serializers.CharField(max_length=20, write_only=True)
 
    class Meta(BaseRegistroSerializer.Meta):
        fields = BaseRegistroSerializer.Meta.fields + ("direccion", "telefono")
 
    def validate_telefono(self, value):
        if not re.fullmatch(r"\+?[0-9\s\-]{6,20}", value):
            raise serializers.ValidationError("Número de teléfono no válido.")
        return value
 
    @transaction.atomic
    def create(self, validated_data):
        direccion = validated_data.pop("direccion")
        telefono = validated_data.pop("telefono")
        password = validated_data.pop("password")
 
        # create_user fija tipo_usuario=cliente, is_staff=False
        user = UsuarioModel.objects.create_user(password=password, **validated_data)
        ClienteUsuarioModel.objects.create(
            user=user, direccion=direccion, telefono=telefono
        )
        return user
 
    def to_representation(self, instance):
        data = super().to_representation(instance)
        perfil = instance.perfil_cliente
        data["direccion"] = perfil.direccion
        data["telefono"] = perfil.telefono
        return data
 
 
class AdminRegistroSerializer(serializers.ModelSerializer):
    """
    El administrador que crea la cuenta NO define la contraseña: la cuenta se
    crea con una contraseña inutilizable y el nuevo usuario recibe por correo
    un enlace para elegir la suya (invitación).
    """
 
    departamento = serializers.CharField(max_length=100, write_only=True)
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
 
    class Meta:
        model = UsuarioModel
        fields = (
            "user_id",
            "email",
            "first_name",
            "last_name",
            "departamento",
            "groups",
        )
        read_only_fields = ("user_id",)
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }
 
    def validate_email(self, value):
        value = UsuarioModel.objects.normalize_email(value).lower()
        if UsuarioModel.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return value
 
    def validate_groups(self, value):
        # Anti-escalada: solo se pueden asignar roles cuyos permisos ya tienes
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            propios = request.user.get_all_permissions()
            for grupo in value:
                for p in grupo.permissions.select_related("content_type"):
                    if f"{p.content_type.app_label}.{p.codename}" not in propios:
                        raise serializers.ValidationError(
                            f'No puedes asignar el rol "{grupo.name}": '
                            "incluye permisos que tú no tienes."
                        )
        return value
 
    def create(self, validated_data):
        departamento = validated_data.pop("departamento")
        groups = validated_data.pop("groups", [])
 
        with transaction.atomic():
            # password=None -> contraseña inutilizable hasta que el usuario
            # defina la suya con el enlace. Nunca se crea un superusuario desde la API.
            user = UsuarioModel.objects.create_user(
                password=None,
                tipo_usuario=UsuarioModel.TipoUsuario.ADMIN,
                is_staff=True,
                **validated_data,
            )
            AdministradorModel.objects.create(user=user, departamento=departamento)
            if groups:
                user.groups.set(groups)
 
        # El correo se envía fuera de la transacción: si falla, la cuenta ya
        # existe y el frontend recibe el aviso para que el usuario pida el enlace
        user._invitacion_enviada = enviar_enlace_password(user, invitacion=True)
        return user
 
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["departamento"] = instance.perfil_admin.departamento
        data["groups"] = list(instance.groups.values_list("name", flat=True))
        data["invitacion_enviada"] = getattr(instance, "_invitacion_enviada", None)
        return data
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    departamento = serializers.CharField(source="perfil_admin.departamento", read_only=True)
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    
    class Meta:
        model = UsuarioModel
        fields = ('user_id', 'email', 'tipo_usuario', 'first_name', 'last_name', 'password', 'departamento', 'groups')
        #read_only_fields = ('user_id', 'tipo_usuario')  # No permitir modificar desde el serializer anidado
        extra_kwargs = {
            'password': {'write_only': True}
        }

class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")

TELEFONO_REGEX = r"\+?[0-9\s\-]{6,20}"
 
 
def _aplicar_cambios(instancia, datos):
    """Asigna los campos recibidos y guarda la instancia."""
    for atributo, valor in datos.items():
        setattr(instancia, atributo, valor)
    instancia.save()
    return instancia
 
 
# ---------------------------------------------------------------------------
# CLIENTE: edita su propio perfil (PATCH /api/store/perfil/)
# ---------------------------------------------------------------------------
class ClienteActualizacionSerializer(serializers.ModelSerializer):
    """
    Se usa con instance=request.user. Los campos del perfil se leen y escriben
    mediante `source`, por lo que aparecen planos en el JSON.
    Campos NO editables: email, tipo_usuario, is_staff, is_superuser, groups.
    """
 
    direccion = serializers.CharField(
        source="perfil_cliente.direccion", max_length=150, required=False
    )
    telefono = serializers.CharField(
        source="perfil_cliente.telefono", max_length=20, required=False
    )
 
    class Meta:
        model = UsuarioModel
        fields = ("user_id", "email", "first_name", "last_name", "direccion", "telefono")
        read_only_fields = ("user_id", "email")
 
    def validate_telefono(self, value):
        if not re.fullmatch(TELEFONO_REGEX, value):
            raise serializers.ValidationError("Número de teléfono no válido.")
        return value
 
    @transaction.atomic
    def update(self, instance, validated_data):
        perfil_data = validated_data.pop("perfil_cliente", {})
        _aplicar_cambios(instance, validated_data)
        if perfil_data:
            _aplicar_cambios(instance.perfil_cliente, perfil_data)
        return instance
 
 
# ---------------------------------------------------------------------------
# ADMIN: edita su propio perfil (PATCH /api/admin/perfil/)
# ---------------------------------------------------------------------------
class AdminPerfilPropioSerializer(serializers.ModelSerializer):
    """El administrador solo cambia su nombre; departamento y grupos los gestiona otro admin."""
 
    departamento = serializers.CharField(
        source="perfil_admin.departamento", read_only=True
    )
 
    class Meta:
        model = UsuarioModel
        fields = ("user_id", "email", "first_name", "last_name", "departamento")
        read_only_fields = ("user_id", "email")
 
 
# ---------------------------------------------------------------------------
# ADMIN: un administrador con permisos gestiona a otro
# (PATCH /api/admin/usuarios/<user_id>/)
# ---------------------------------------------------------------------------
class AdminActualizacionSerializer(serializers.ModelSerializer):
    departamento = serializers.CharField(
        source="perfil_admin.departamento", max_length=100, required=False
    )
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False
    )
 
    class Meta:
        model = UsuarioModel
        fields = (
            "user_id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "departamento",
            "groups",
        )
        read_only_fields = ("user_id", "email")
 
    # def validate_groups(self, value):
    #     # Evita escalada de privilegios: un admin con permiso de edición
    #     # no debería poder darse (o dar) grupos más poderosos.
    #     request = self.context.get("request")
    #     if request and not request.user.is_superuser:
    #         raise serializers.ValidationError(
    #             "Solo un superusuario puede modificar los grupos."
    #         )
    #     return value
    def validate_groups(self, value):
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            propios = request.user.get_all_permissions()
            for grupo in value:
                for p in grupo.permissions.select_related("content_type"):
                    if f"{p.content_type.app_label}.{p.codename}" not in propios:
                        raise serializers.ValidationError(
                            f'No puedes asignar el rol "{grupo.name}": '
                            "incluye permisos que tú no tienes."
                        )
        return value
 
    def validate_is_active(self, value):
        request = self.context.get("request")
        if request and self.instance == request.user and value is False:
            raise serializers.ValidationError("No puedes desactivar tu propia cuenta.")
        return value
 
    @transaction.atomic
    def update(self, instance, validated_data):
        perfil_data = validated_data.pop("perfil_admin", {})
        groups = validated_data.pop("groups", None)
 
        _aplicar_cambios(instance, validated_data)
        if perfil_data:
            _aplicar_cambios(instance.perfil_admin, perfil_data)
        if groups is not None:
            instance.groups.set(groups)
        return instance
 
 
