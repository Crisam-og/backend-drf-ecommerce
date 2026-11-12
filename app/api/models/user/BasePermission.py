from rest_framework.permissions import BasePermission

class EsCliente(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.tipo_usuario == "cliente")

class EsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_staff
                and request.user.tipo_usuario == "admin")