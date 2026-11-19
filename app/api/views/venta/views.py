from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from api.models.venta.models import VentaModel
from api.serializers.venta.serializer import VentaSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db.models import Sum, Max
from django.utils import timezone

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models.empresa.models import EmpresaModel


from api.views.venta.comprobantepdf import generar_comprobante_pdf



class VentaViewSet(viewsets.ModelViewSet):
    # Corregido: modelo VentaModel y sin select_related("cliente") (es un CharField)
    queryset = VentaModel.objects.prefetch_related(
        "detalles__producto", "detalles__presentacion"
    ).order_by("-fecha_venta")
    serializer_class = VentaSerializer

    @action(detail=True, methods=["get"])
    def detalles(self, request, pk=None):
        
        return Response(VentaSerializer(self.get_object()).data)

    # GET /api/ventas/<id>/comprobante/            -> PDF para ver en el navegador
    # GET /api/ventas/<id>/comprobante/?download=1 -> PDF como descarga
    @action(detail=True, methods=["get"])
    def comprobante(self, request, pk=None):
        venta = self.get_object()
        empresa = EmpresaModel.objects.first()
        
        pdf = generar_comprobante_pdf(venta, empresa)

        nombre = venta.numero_comprobante if venta.numero else str(venta.venta_id)
        disposicion = "attachment" if request.query_params.get("download") else "inline"

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'{disposicion}; filename="{nombre}.pdf"'
        return response

class ListarVentasApi(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        es_admin = user.is_superuser or user.groups.filter(name='Administrador').exists()
        ventas = VentaModel.objects.prefetch_related(
            "detalles__producto", 
            "detalles__presentacion"
        ).order_by("-fecha_venta")
        # Si no es admin, filtramos solo sus ventas
        if not es_admin:
            ventas = ventas.filter(usuario=user)

        inversion = 655
        hoy = timezone.now()
        sum_total_ventas = VentaModel.objects.filter(fecha_venta__year=hoy.year, fecha_venta__month=hoy.month).aggregate(Sum("total", default=0))
        resultado_total_ventas = sum_total_ventas["total__sum"]
        ganancia_total = sum_total_ventas["total__sum"] - inversion
        # user = request.user
        # grupos = list(user.groups.values_list('name', flat=True))
        # print(f"Grupos del usuario logueado:", grupos)
        print(f"Suma de todos los totales de la venta es: ", resultado_total_ventas)
        print(f"Ganancia Total es: ", ganancia_total)
        #print(f"Ventas", ventas)
        search = request.query_params.get("search")
        # resumen_por_dni = (
        #     VentaModel.objects
        #     .exclude(dni_cliente='')  # Ignora ventas donde no se registró DNI
        #     .values('dni_cliente')    # Agrupa estrictamente por el número de DNI
        #     .annotate(
        #         nombre_cliente=Max('cliente'),  # Toma un nombre asociado a ese DNI
        #         total_gastado=Sum('total')      # Suma todas sus compras
        #     )
        #     .order_by('-total_gastado')
        # )
        
        # for registro in resumen_por_dni:
        #     print(f"DNI: {registro['dni_cliente']} | Nombre: {registro['nombre_cliente']} | Total: S/ {registro['total_gastado']}")

        if search:
            ventas = ventas.filter(Q(cliente__icontains=search) | Q(dni_cliente__icontains=search) | Q(ruc_cliente__icontains=search))

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 100
        pagina = paginator.paginate_queryset(ventas, request, view=self)
        serializer = VentaSerializer(pagina, many=True)
        return Response({
            "message": "Lista de ventas obtenida exitosamente.",
            "data": serializer.data,
            "total_ventas": paginator.page.paginator.count,
            "sum_total_ventas": resultado_total_ventas,
            "inversion": inversion,
            "ganancia_total": ganancia_total,
            "page": paginator.page.number,
            "page_size": paginator.get_page_size(request),
            "total_paginas": paginator.page.paginator.num_pages,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        }, status=status.HTTP_200_OK)
