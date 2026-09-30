from django.db import models
import uuid

class ContactoModel(models.Model):
    contacto_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    telefono = models.CharField(max_length=9)
    correo = models.EmailField()
    mensaje = models.TextField(max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contacto"
        verbose_name_plural = "Contacto"
    
    def __str__(self):
        return self.name
    