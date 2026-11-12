#Seccion para categorias
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from api.serializers.categoria.serializer import CategoriaSerializer, RegistroCategoriaSerializer, ActualizarCategoriaSerializer
from api.models.producto.models import CategoriaModel
from django.db.models import Count
from rest_framework import generics, filters

class CategoriaPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    # Opcional: Personaliza la estructura de la respuesta si quieres mantener tu formato exacto
    def get_paginated_response(self, data):
        print(data)
        return Response({
            'message': 'Lista de categorias obtenida exitosamente.',
            'data': data,
            'total_categorias': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'total_paginas': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
        }, status=status.HTTP_200_OK)

class ListarCategoriasApi(generics.ListCreateAPIView):
    queryset = CategoriaModel.objects.annotate(product_count=Count('productos'))
    pagination_class = CategoriaPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']   
    serializer_class = CategoriaSerializer

class RegistroCategoriaApi(generics.CreateAPIView):
    queryset = CategoriaModel.objects.all()
    serializer_class = RegistroCategoriaSerializer

class ActualizarCategoriaApi(generics.UpdateAPIView):
    queryset = CategoriaModel.objects.all()
    serializer_class = ActualizarCategoriaSerializer
    #permission_classes = [AllowAny]

class DetalleCategoriaApi(generics.RetrieveAPIView):
    queryset = CategoriaModel.objects.all()
    serializer_class = CategoriaSerializer