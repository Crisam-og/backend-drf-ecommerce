from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Count
from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
 
from api.models.user.BasePermission import EsAdministrador
from api.serializers.permisos.serializer import PermisoSerializer, RolSerializer
from api.models.user.Roles import permisos_asignables, etiqueta_permiso, PuedeVerRoles, RolPermission


class PermisoListView(generics.ListAPIView):
    """GET /api/admin/permisos/ -> catálogo de permisos asignables a un rol."""
 
    serializer_class = PermisoSerializer
    permission_classes = [EsAdministrador, PuedeVerRoles]
    pagination_class = None
 
    def get_queryset(self):
        return permisos_asignables()
 
 
class RolViewSet(viewsets.ModelViewSet):
    """CRUD de roles (django.contrib.auth.models.Group)."""
 
    serializer_class = RolSerializer
    permission_classes = [EsAdministrador, RolPermission]
    pagination_class = None
    queryset = (
        Group.objects.annotate(num_usuarios=Count("user", distinct=True))
        .prefetch_related("permissions")
        .order_by("name")
    )
 
    def _validar_alcance(self, rol):
        """Un no-superusuario no puede tocar un rol con permisos que él no tiene."""
        user = self.request.user
        if user.is_superuser:
            return
        propios = user.get_all_permissions()
        if any(etiqueta_permiso(p) not in propios for p in rol.permissions.select_related("content_type")):
            raise PermissionDenied(
                "Este rol incluye permisos que tú no tienes, por lo que no puedes modificarlo."
            )
 
    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
 
    @transaction.atomic
    def perform_update(self, serializer):
        self._validar_alcance(serializer.instance)
        serializer.save()
 
    def destroy(self, request, *args, **kwargs):
        rol = self.get_object()
        self._validar_alcance(rol)
 
        usuarios = rol.user_set.count()
        if usuarios:
            return Response(
                {
                    "detail": f"No se puede eliminar: {usuarios} usuario(s) tienen este rol. "
                    "Reasígnalos primero."
                },
                status=409,
            )
        rol.delete()
        return Response(status=204)