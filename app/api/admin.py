# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from api.models.producto.models import ProductoModel, CategoriaModel
from api.models.user.models import AdministradorModel, ClienteUsuarioModel, UsuarioModel

#admin.site.register(UsuarioModel)
#admin.site.register(ClienteUsuarioModel)
#admin.site.register(AdministradorModel)
admin.site.register(ProductoModel)
admin.site.register(CategoriaModel)
# admin.site.register(ClienteUsuarioModel)
# admin.site.register(AdministradorModel)
# ---------------------------------------------------------------------------
# Formularios: los de Django asumen `username`, hay que apuntarlos a tu modelo
# ---------------------------------------------------------------------------
class UsuarioCreationForm(UserCreationForm):
    class Meta:
        model = UsuarioModel
        fields = ("email", "tipo_usuario")


class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = UsuarioModel
        fields = "__all__"


# ---------------------------------------------------------------------------
# Inlines de perfil
# ---------------------------------------------------------------------------
class ClienteInline(admin.StackedInline):
    model = ClienteUsuarioModel
    can_delete = False
    verbose_name_plural = "Perfil de cliente"


class AdministradorInline(admin.StackedInline):
    model = AdministradorModel
    can_delete = False
    verbose_name_plural = "Perfil de administrador"


# ---------------------------------------------------------------------------
# Admin de usuarios
# ---------------------------------------------------------------------------
@admin.register(UsuarioModel)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    model = UsuarioModel

    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "tipo_usuario",
        "is_staff",
        "is_active",
    )
    list_filter = ("tipo_usuario", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("user_id", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("user_id", "email", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name")}),
        ("Tipo de usuario", {"fields": ("tipo_usuario",)}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "tipo_usuario", "password1", "password2"),
            },
        ),
    )

    def get_inlines(self, request, obj):
        """
        Muestra el perfil según el tipo de usuario. En la vista de creación
        no hay inline: primero se crea el usuario y luego se completa el perfil.
        """
        if obj is None:
            return []
        if obj.tipo_usuario == UsuarioModel.TipoUsuario.CLIENTE:
            return [ClienteInline]
        if obj.tipo_usuario == UsuarioModel.TipoUsuario.ADMIN:
            return [AdministradorInline]
        return []


# ---------------------------------------------------------------------------
# Admin de perfiles (opcional, útil para consultar y buscar)
# ---------------------------------------------------------------------------
@admin.register(ClienteUsuarioModel)
class ClienteUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "telefono", "direccion")
    search_fields = ("user__email", "telefono")
    raw_id_fields = ("user",)


@admin.register(AdministradorModel)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ("user", "departamento")
    search_fields = ("user__email", "departamento")
    raw_id_fields = ("user",)
