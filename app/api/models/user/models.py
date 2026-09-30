from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

class UsuarioModel(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = None  # Remove username field
    TIPO_USUARIO_CHOICES = (
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
    )

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # 👈 nada extra requerido
    def __str__(self):
        return self.email
    
class ClienteUsuarioModel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    direccion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"Cliente: {self.user.email}"

class AdministradorModel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    departamento = models.CharField(max_length=100)

    def __str__(self):
        return f"Admin: {self.user.email}"