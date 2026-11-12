from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from api.models.user.Roles import permisos_asignables, etiqueta_permiso, ACCIONES_ESTANDAR  

class PermisoSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source="content_type.app_label")
    model = serializers.CharField(source="content_type.model")
    model_label = serializers.SerializerMethodField()
    accion = serializers.SerializerMethodField()
 
    class Meta:
        model = Permission
        fields = ("id", "codename", "name", "app_label", "model", "model_label", "accion")
 
    def get_model_label(self, obj):
        clase = obj.content_type.model_class()
        if clase is None:
            return obj.content_type.model
        return str(clase._meta.verbose_name_plural).capitalize()
 
    def get_accion(self, obj):
        # 'view' | 'add' | 'change' | 'delete' si el codename sigue el patrón
        # estándar "<accion>_<modelo>"; cualquier otro es un permiso propio ("otro")
        prefijo = obj.codename.split("_", 1)[0]
        if prefijo in ACCIONES_ESTANDAR and obj.codename == f"{prefijo}_{obj.content_type.model}":
            return prefijo
        return "otro"
 
 
class RolSerializer(serializers.ModelSerializer):
    permisos = serializers.PrimaryKeyRelatedField(
        source="permissions",
        many=True,
        required=False,
        queryset=Permission.objects.all(),
    )
    num_usuarios = serializers.IntegerField(read_only=True)
 
    class Meta:
        model = Group
        fields = ("id", "name", "permisos", "num_usuarios")
 
    def validate_name(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")
        existe = Group.objects.filter(name__iexact=value)
        if self.instance:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise serializers.ValidationError("Ya existe un rol con este nombre.")
        return value
 
    def validate_permisos(self, value):
        asignables = set(permisos_asignables().values_list("pk", flat=True))
        if any(p.pk not in asignables for p in value):
            raise serializers.ValidationError("Algunos permisos no existen o no se pueden asignar.")
 
        # Anti-escalada: nadie puede conceder un permiso que él mismo no tiene
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            propios = request.user.get_all_permissions()
            if any(etiqueta_permiso(p) not in propios for p in value):
                raise serializers.ValidationError(
                    "No puedes asignar permisos que tú no tienes."
                )
        return value