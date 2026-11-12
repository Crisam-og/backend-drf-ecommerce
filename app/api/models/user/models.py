import uuid
 
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
 
 
class UsuarioManager(BaseUserManager):
    """Manager para un usuario sin `username`, autenticado por email."""
 
    use_in_migrations = True
 
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
 
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("tipo_usuario", UsuarioModel.TipoUsuario.CLIENTE)
        return self._create_user(email, password, **extra_fields)
 
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("tipo_usuario", UsuarioModel.TipoUsuario.ADMIN)
 
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True")
 
        return self._create_user(email, password, **extra_fields)
 
 
class UsuarioModel(AbstractUser):
    """
    Usuario base. Los roles finos de los administradores se manejan con
    Groups y Permissions de Django (heredados de AbstractUser/PermissionsMixin).
    """
 
    class TipoUsuario(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        ADMIN = "admin", "Administrador"
 
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = None  # Se elimina el campo username
 
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.CLIENTE,
        db_index=True,
    )
 
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Nada extra requerido para createsuperuser
 
    objects = UsuarioManager()
 
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
 
    def __str__(self):
        return self.email
 
    @property
    def es_cliente(self):
        return self.tipo_usuario == self.TipoUsuario.CLIENTE
 
    @property
    def es_administrador(self):
        return self.tipo_usuario == self.TipoUsuario.ADMIN and self.is_staff
 
    def save(self, *args, **kwargs):
        # Mantiene coherencia: los admins siempre son staff; los clientes nunca.
        if self.tipo_usuario == self.TipoUsuario.ADMIN:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)
 
 
class ClienteUsuarioModel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_cliente",
    )
    direccion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
 
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
 
    def clean(self):
        if self.user_id and self.user.tipo_usuario != UsuarioModel.TipoUsuario.CLIENTE:
            raise ValidationError("El usuario asociado debe ser de tipo cliente.")
 
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"Cliente: {self.user.email}"
 
 
class AdministradorModel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_admin",
    )
    departamento = models.CharField(max_length=100)
 
    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
 
    def clean(self):
        if self.user_id and self.user.tipo_usuario != UsuarioModel.TipoUsuario.ADMIN:
            raise ValidationError("El usuario asociado debe ser de tipo administrador.")
 
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"Admin: {self.user.email}"