from django.db import models
import uuid
from solo.models import SingletonModel

# class EmpresaManager(models.Manager):
#     """
#     Manager personalizado para manejar el patrón Singleton.
#     """
#     def get_instance(self):
#         """
#         Obtiene la única instancia de Empresa si existe, sino retorna None.
#         """
#         return self.first()
    
class EmpresaModel(SingletonModel):
    #empresa_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)
    telefono = models.CharField(max_length=9)
    correo = models.EmailField()
    direccion = models.CharField(max_length=150)
    url_whatsapp = models.URLField()
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    #objects = EmpresaManager()
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresa"
    
    # def save(self, *args, **kwargs):
    #     """
    #     Asegura que solo exista una instancia de Empresa.
    #     """
    #     if not self.pk:
    #         existing = EmpresaModel.objects.first()
    #         if existing:
    #             self.empresa_id = existing.empresa_id
    #     super().save(*args, **kwargs)
    
    # def delete(self, *args, **kwargs):
    #     """
    #     Previene la eliminación de la empresa.
    #     """
    #     pass
    
    def __str__(self):
        return self.nombre