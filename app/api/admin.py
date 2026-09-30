from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin
from api.models.user.models import UsuarioModel, ClienteUsuarioModel, AdministradorModel
from api.models.producto.models import ProductoModel, CategoriaModel


admin.site.register(UsuarioModel)
admin.site.register(ClienteUsuarioModel)
admin.site.register(AdministradorModel)
admin.site.register(ProductoModel)
admin.site.register(CategoriaModel)
# Register your models here.
