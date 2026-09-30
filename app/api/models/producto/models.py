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

class ProductoModel(models.Model):
    producto_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(CategoriaModel, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=150)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00, validators=[MinValueValidator(0)])
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    peso = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00, validators=[MinValueValidator(0)])
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_url = models.URLField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre
    

