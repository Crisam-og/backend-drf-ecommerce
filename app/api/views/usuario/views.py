from rest_framework import generics
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from api.serializers.usuario.serializer import ClienteRegistroSerializer, AdminRegistroSerializer, UsuarioSerializer,AdminActualizacionSerializer, GrupoSerializer
from api.models.user.models import UsuarioModel
from api.models.user.BasePermission import EsAdministrador
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics, filters
from django.contrib.auth.models import Group

class UserPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    # Opcional: Personaliza la estructura de la respuesta si quieres mantener tu formato exacto
    def get_paginated_response(self, data):
        print(data)
        return Response({
            'message': 'Lista de usuarios obtenida exitosamente.',
            'data': data,
            'total_usuarios': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'total_paginas': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
        }, status=status.HTTP_200_OK)
class RegistroClienteView(generics.CreateAPIView):
    serializer_class = ClienteRegistroSerializer
    permission_classes = [AllowAny]

class RegistroAdminView(generics.CreateAPIView):
    queryset = UsuarioModel.objects.all()  # requerido por DjangoModelPermissions
    serializer_class = AdminRegistroSerializer
    permission_classes = [EsAdministrador, DjangoModelPermissions]

class UserListApi(generics.ListCreateAPIView):
    queryset = UsuarioModel.objects.order_by('first_name')
    pagination_class = UserPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['email']   
    serializer_class = UsuarioSerializer

class UserDetail(generics.RetrieveAPIView):
    queryset = UsuarioModel.objects.all()
    serializer_class = UsuarioSerializer
    #lookup_field = 'user_id' 
    # Cambiamos el serializador dinámicamente si van a actualizar (PUT)

class UpdateUserApi(generics.UpdateAPIView):
    queryset = UsuarioModel.objects.all()
    serializer_class = AdminActualizacionSerializer
    #permission_classes = [EsAdministrador, DjangoModelPermissions]

class GrupoListView(generics.ListAPIView):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GrupoSerializer
    permission_classes = [EsAdministrador]
    pagination_class = None