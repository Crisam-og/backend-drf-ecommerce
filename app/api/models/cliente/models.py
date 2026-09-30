from django.db import models
import uuid

class ClienteModel(models.Model):
    cliente_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(blank=True, null=True)
    descripcion = models.CharField(max_length=150)
    sitio_web = models.URLField(blank=True) 
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre


