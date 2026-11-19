import uuid
from django.db import models
from api.models.user.models import UsuarioModel
from api.models.producto.models import ProductoModel, ProductoPresentacionModel

class EntradaModel(models.Model):
    class TipoComprobante(models.TextChoices):
            FACTURA = "F", "Factura"
    entrada_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(UsuarioModel, on_delete=models.PROTECT)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_emision = models.DateField()
    proveedor = models.CharField(max_length=50)
    ruc = models.CharField(max_length=11)
    tipo_comprobante = models.CharField(max_length=1, choices=TipoComprobante.choices, default=TipoComprobante.FACTURA)
    numero_comprobante = models.CharField(max_length=50)
    # Solo los 4 totales del pie de factura (toma 5 segundos digitarlos)
    subtotal_gravado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    igv = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    percepcion = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    imagen_comprobante = models.FileField(upload_to='comprobantes/%Y/%m/', blank=True, null=True)
    observaciones= models.CharField(max_length=500, blank=True, null=True)

    class Meta:
          verbose_name="Entrada"
          verbose_name_plural="Entradas"

class EntradaDetalleModel(models.Model):
      detalle_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
      entrada = models.ForeignKey(EntradaModel, on_delete=models.CASCADE, related_name="detalles") 
      producto = models.ForeignKey(ProductoModel, on_delete=models.PROTECT)
      presentacion = models.ForeignKey(ProductoPresentacionModel, on_delete=models.PROTECT, related_name='entradas_detalle')
      # Snapshot al momento de registrar el nuevo ingreso
      nombre_presentacion = models.CharField(max_length=30, default="Unidad")
      unidades_por_presentacion = models.PositiveIntegerField(default=1)
      fecha_vencimiento = models.DateField()
      cantidad = models.PositiveIntegerField(default=1)
      costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
      subtotal = models.DecimalField(max_digits=10, decimal_places=2)

      class Meta:
            verbose_name="Detalle de Entrada"
            verbose_name_plural="Detalle de Entradas"