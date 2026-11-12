from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from api.serializers.producto.serializer import ProductoSerializer, RegistroProductoSerializer, ActualizarProductoSerializer
from api.models.producto.models import ProductoModel

class RegistroProductoApi(APIView):
    def post(self, request):
        serializer = RegistroProductoSerializer(data=request.data)
        if serializer.is_valid():
            producto = serializer.save()
            return Response(ProductoSerializer(producto).data, status=status.HTTP_201_CREATED)
        print("Errores de validación:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ListarProductosApi(APIView):
    def get(self, request):
        productos = ProductoModel.objects.order_by('nombre')
        search_query = request.query_params.get('search', None)
        
        if search_query:
            productos = productos.filter(nombre__icontains=search_query)

        # Permite controlar el tamaño de página mediante ?page_size=; se limita
        # para evitar respuestas excesivamente grandes.
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        pagina_productos = paginator.paginate_queryset(productos, request, view=self)
        serializer = ProductoSerializer(pagina_productos, many=True)
        return Response({
            'message': 'Lista de productos obtenida exitosamente.',
            'data': serializer.data,
            'total_productos': paginator.page.paginator.count,
            'page': paginator.page.number,
            'page_size': paginator.get_page_size(request),
            'total_paginas': paginator.page.paginator.num_pages,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),      
            #'total_productos': productos.count()
        }, status=status.HTTP_200_OK)
class ActualizarProductoApi(APIView):
    def put(self, request, pk):
        try:
            producto = ProductoModel.objects.get(producto_id=pk)
        except ProductoModel.DoesNotExist:
            return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ActualizarProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            producto_actualizado = serializer.save()
            return Response(ProductoSerializer(producto_actualizado).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class EliminarProductoApi(APIView):
    def delete(self, request, pk):
        try:
            producto = ProductoModel.objects.get(producto_id=pk)
        except ProductoModel.DoesNotExist:
            return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        producto.delete()
        return Response({'message': 'Producto eliminado exitosamente.'}, status=status.HTTP_200_OK)
class DetalleProductoApi(APIView):
    def get(self, request, pk):
        try:
            producto = ProductoModel.objects.get(producto_id=pk)
        except ProductoModel.DoesNotExist:
            return Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductoSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)


# class RegistroCategoriaApi(APIView):
#     def post(self, request):
#         serializer = RegistroCategoriaSerializer(data=request.data)
#         if serializer.is_valid():
#             categoria = serializer.save()
#             return Response(RegistroCategoriaSerializer(categoria).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

# from rest_framework import generics, filters
# from rest_framework.pagination import PageNumberPagination
# from rest_framework.response import Response
# from rest_framework import status

# # 1. Definimos la paginación personalizada (para mantener tus reglas)
# class ProductoPagination(PageNumberPagination):
#     page_size = 5
#     page_size_query_param = 'page_size'
#     max_page_size = 100

#     # Opcional: Personaliza la estructura de la respuesta si quieres mantener tu formato exacto
#     def get_paginated_response(self, data):
#         return Response({
#             'message': 'Lista de productos obtenida exitosamente.',
#             'data': data,
#             'total_productos': self.page.paginator.count,
#             'page': self.page.number,
#             'page_size': self.get_page_size(self.request),
#             'total_paginas': self.page.paginator.num_pages,
#             'next': self.get_next_link(),
#             'previous': self.get_previous_link(),
#         }, status=status.HTTP_200_OK)

# # 2. La vista se reduce drásticamente
# class ListarProductosApi(generics.ListAPIView):
#     queryset = ProductoModel.objects.order_by('nombre')
#     serializer_class = ProductoSerializer
#     pagination_class = ProductoPagination
    
#     # DRF maneja el filtro de búsqueda de forma nativa agregando esto:
#     filter_backends = [filters.SearchFilter]
#     search_fields = ['nombre'] # Mismo comportamiento que nombre__icontains