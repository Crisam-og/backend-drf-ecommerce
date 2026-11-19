from django.db import models
from django.core.validators import MinValueValidator
import uuid


class CategoriaModel(models.Model):
    categoria_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=150)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nombre

# class ProductoModel(models.Model):
#     producto_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     categoria = models.ForeignKey(CategoriaModel, on_delete=models.CASCADE, related_name='productos')
#     nombre = models.CharField(max_length=50, unique=True)
#     descripcion = models.CharField(max_length=150)
#     precio = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00, validators=[MinValueValidator(0)])
#     stock = models.IntegerField(validators=[MinValueValidator(0)])
#     peso = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00, validators=[MinValueValidator(0)])
#     imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
#     imagen_url = models.URLField(blank=True, null=True)
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    
#     class Meta:
#         verbose_name = "Producto"
#         verbose_name_plural = "Productos"

#     def __str__(self):
#         return self.nombre
    
class ProductoModel(models.Model):
    """Qué es el producto (datos comunes a todas sus presentaciones)."""
    producto_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(CategoriaModel, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=50, unique=True)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])  # en unidades base
    descripcion = models.CharField(max_length=150)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_url = models.URLField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
    def __str__(self):
        return self.nombre

class ProductoPresentacionModel(models.Model):
    """Cómo se vende: unidad, six pack, docena, etc."""
    presentacion_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey(ProductoModel, on_delete=models.CASCADE, related_name='presentaciones')
    nombre = models.CharField(max_length=30)  # "Unidad", "Six pack", "Docena"
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    unidades_por_presentacion = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Presentación de Producto"
        verbose_name_plural = "Presentación de Productos"
        constraints = [
            models.UniqueConstraint(fields=['producto', 'nombre'], name='unique_presentacion_por_producto'),
        ]

    @property
    def stock_disponible(self):
        return self.producto.stock // self.unidades_por_presentacion

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre} - {self.sku}"
