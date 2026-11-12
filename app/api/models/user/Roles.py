from django.contrib.auth.models import Permission
from rest_framework.permissions import BasePermission, DjangoModelPermissions


# ---------------------------------------------------------------------------
# Qué permisos se pueden asignar a un rol
# Se ocultan los de tablas internas de Django/librerías: no tiene sentido
# que un rol "edite sesiones" o "elimine tokens".
# ---------------------------------------------------------------------------
APPS_EXCLUIDAS = {"admin", "contenttypes", "sessions", "token_blacklist"}
ACCIONES_ESTANDAR = {"view", "add", "change", "delete"}
 
 
def permisos_asignables():
    return (
        Permission.objects.select_related("content_type")
        .exclude(content_type__app_label__in=APPS_EXCLUIDAS)
        .exclude(content_type__app_label="auth", content_type__model="permission")
        .order_by("content_type__app_label", "content_type__model", "codename")
    )
 
 
def etiqueta_permiso(p: Permission) -> str:
    """'app_label.codename', el mismo formato que user.get_all_permissions()."""
    return f"{p.content_type.app_label}.{p.codename}"
 
 
# ---------------------------------------------------------------------------
# Clases de permiso DRF
# ---------------------------------------------------------------------------
class PuedeVerRoles(BasePermission):
    """Para listar el catálogo de permisos: exige poder ver roles."""
 
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm("auth.view_group")
 
 
class RolPermission(DjangoModelPermissions):
    """
    DjangoModelPermissions deja pasar los GET sin exigir nada. Aquí ver roles
    también exige el permiso `auth.view_group`.
    """
 
    perms_map = {
        **DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
    }