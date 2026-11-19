from django.db import models
import uuid
from api.models.producto.models import ProductoModel, ProductoPresentacionModel
from api.models.user.models import UsuarioModel
#from api.models.empresa.models import EmpresaModel

class SerieComprobanteModel(models.Model):
    """Correlativo por tipo de comprobante (B001, F001...)."""

    tipo = models.CharField(max_length=1, unique=True)  # "B" o "F"
    serie = models.CharField(max_length=4)
    ultimo_numero = models.PositiveIntegerField(default=0)

    @classmethod
    def siguiente(cls, tipo):
        """Debe llamarse dentro de transaction.atomic(): bloquea la fila para
        que dos ventas simultáneas no obtengan el mismo número."""
        defaults = {"serie": "F001" if tipo == "F" else "B001"}
        obj, _ = cls.objects.get_or_create(tipo=tipo, defaults=defaults)
        obj = cls.objects.select_for_update().get(pk=obj.pk)
        obj.ultimo_numero += 1
        obj.save(update_fields=["ultimo_numero"])
        return obj.serie, obj.ultimo_numero


class VentaModel(models.Model):
    class TipoComprobante(models.TextChoices):
        BOLETA = "B", "Boleta"
        FACTURA = "F", "Factura"

    venta_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(UsuarioModel, on_delete=models.PROTECT, blank=True, null=True)
    tipo_comprobante = models.CharField(
        max_length=1, choices=TipoComprobante.choices, default=TipoComprobante.BOLETA
    )
    serie = models.CharField(max_length=4, blank=True)
    numero = models.PositiveIntegerField(null=True, blank=True)

    cliente = models.CharField(max_length=100)  # nombre o razón social
    dni_cliente = models.CharField(max_length=8, blank=True)  # ahora opcional (factura)
    ruc_cliente = models.CharField(max_length=11, blank=True)
    direccion_cliente = models.CharField(max_length=200, blank=True)

    fecha_venta = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    igv = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        constraints = [
            models.UniqueConstraint(fields=["serie", "numero"], name="uniq_serie_numero")
        ]

    @property
    def numero_comprobante(self) -> str:
        # Ventas anteriores a este cambio no tienen serie/número
        if self.numero:
            return f"{self.serie}-{self.numero:08d}"
        return "SIN NUMERAR"

    def __str__(self):
        return f"{self.numero_comprobante} - {self.cliente} - Total: {self.total}"

class VentaDetalleModel(models.Model):
    ventadet_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venta = models.ForeignKey(VentaModel, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(ProductoModel, on_delete=models.PROTECT)
    presentacion = models.ForeignKey(
        ProductoPresentacionModel, on_delete=models.PROTECT,
        null=True, blank=True, related_name='ventas_detalle',
    )
    # Snapshot al momento de la venta
    nombre_presentacion = models.CharField(max_length=30, default="Unidad")
    unidades_por_presentacion = models.PositiveIntegerField(default=1)

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # precio de la presentación
    cantidad = models.PositiveIntegerField()  # cantidad de presentaciones vendidas
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Venta Detalle"
        verbose_name_plural = "Detalles de Ventas"

    @property
    def unidades_totales(self) -> int:
        return self.cantidad * self.unidades_por_presentacion

    def __str__(self):
        return (f"{self.producto.nombre} ({self.nombre_presentacion}) "
                f"x{self.cantidad} - Subtotal: {self.subtotal}")