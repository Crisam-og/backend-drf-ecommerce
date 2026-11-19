from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from api.serializers.entradas.serializer import EntradaSerializer
from django.utils import timezone
from django.db.models import Q

from api.models.entradas.models import EntradaModel

TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "application/pdf"}
MAX_BYTES = 5 * 1024 * 1024


class EntradaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        EntradaModel.objects.select_related("usuario")
        .prefetch_related("detalles__producto", "detalles__presentacion")
        .order_by("-fecha_ingreso")
    )
    serializer_class = EntradaSerializer

    @action(detail=True, methods=["get"])
    def detalles(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)

    # POST /admin/entradas/<id>/comprobante/  (multipart, campo "imagen_comprobante")
    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def comprobante(self, request, pk=None):
        entrada = self.get_object()
        archivo = request.FILES.get("imagen_comprobante")
        if not archivo:
            return Response({"imagen_comprobante": ["Adjunta un archivo."]}, status=400)
        if archivo.content_type not in TIPOS_PERMITIDOS:
            return Response({"imagen_comprobante": ["Solo JPG, PNG o PDF."]}, status=400)
        if archivo.size > MAX_BYTES:
            return Response({"imagen_comprobante": ["El archivo supera 5 MB."]}, status=400)

        entrada.imagen_comprobante = archivo
        entrada.save(update_fields=["imagen_comprobante"])
        return Response(self.get_serializer(entrada).data)

class ListarEntradasApi(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        es_admin = user.is_superuser or user.groups.filter(name='Administrador').exists()
        entrada = EntradaModel.objects.prefetch_related(
            "detalles__producto", 
            "detalles__presentacion"
        ).order_by("-fecha_ingreso")
        # Si no es admin, filtramos solo sus ventas
        if not es_admin:
            entrada = entrada.filter(usuario=user)
            
        search = request.query_params.get("search")
        if search:
            entrada = entrada.filter(Q(ruc__icontains=search))

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 100
        pagina = paginator.paginate_queryset(entrada, request, view=self)
        serializer = EntradaSerializer(pagina, many=True)
        return Response({
            "message": "Lista de ventas obtenida exitosamente.",
            "data": serializer.data,
            "total_entradas": paginator.page.paginator.count,
            "page": paginator.page.number,
            "page_size": paginator.get_page_size(request),
            "total_paginas": paginator.page.paginator.num_pages,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        }, status=status.HTTP_200_OK)
