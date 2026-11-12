from django.urls import path
from django.urls import include
from django.contrib import admin
from api.views.usuario.views import RegistroClienteView,RegistroAdminView, UserListApi, UserDetail, UpdateUserApi, GrupoListView
from rest_framework_simplejwt.views import TokenRefreshView
from api.views.login.views import AdminLoginView, ClienteLoginView, LogoutView, AdminMeView
from api.views.producto.views import RegistroProductoApi, ActualizarProductoApi, ListarProductosApi, EliminarProductoApi, DetalleProductoApi
from api.views.categoria.views import ListarCategoriasApi, RegistroCategoriaApi, ActualizarCategoriaApi, DetalleCategoriaApi
from api.views.empresa.views import EmpresaView
from django.conf import settings
from django.contrib.staticfiles.urls import static
from api.views.resetpassword.views import PasswordResetRequestView, PasswordResetConfirmView, PasswordResetValidateView
from rest_framework.routers import SimpleRouter
from api.views.permisos.views import RolViewSet, PermisoListView

router = SimpleRouter()
router.register("admin/roles", RolViewSet, basename="rol")
urlpatterns = [
    path('registro/cliente/', RegistroClienteView.as_view(), name='registro-cliente'),
    # path('actualizar/cliente/<uuid:pk>/', ActualizarClienteView.as_view(), name='actualizar-cliente'),
    # path('obtener/cliente/<uuid:pk>/', ObtenerClienteView.as_view(), name='obtener-cliente'),
    # path('eliminar/cliente/<uuid:pk>/', EliminarClienteView.as_view(), name='eliminar-cliente'), 

    #urls para administradores
    path('registro/admin/', RegistroAdminView.as_view(), name='registro-admin'),
    path("usuarios/lista/", UserListApi.as_view()),
    path('detail/user/<uuid:pk>/', UserDetail.as_view(), name='obtener-admin'),
    path('actualizar/usuario/<uuid:pk>/', UpdateUserApi.as_view(), name='actualizar-admin'),
    path("grupos/admin/", GrupoListView.as_view()),

    #urls para productos
    path('producto/registro/', RegistroProductoApi.as_view(), name='registro-producto'),
    path('producto/actualizar/<uuid:pk>/', ActualizarProductoApi.as_view(), name='actualizar-producto'),
    path('producto/listar/', ListarProductosApi.as_view(), name='listar-productos'),
    path('producto/eliminar/<uuid:pk>/', EliminarProductoApi.as_view(), name='eliminar-producto'),
    path('producto/detalle/<uuid:pk>/', DetalleProductoApi.as_view(), name='detalle-producto'),

    #urls para categorias
    path('categoria/registro/', RegistroCategoriaApi.as_view(), name='registro-categoria'),
    path('categoria/actualizar/<uuid:pk>/', ActualizarCategoriaApi.as_view(), name='actualizar-categoria'),
    path('categoria/detalle/<uuid:pk>/', DetalleCategoriaApi.as_view(), name='detalle-categoria'),
    path('categoria/listar/', ListarCategoriasApi.as_view(), name='listar-categorias'),

    #urls para empresa
    path('empresa/', EmpresaView.as_view(), name='empresa'),
    #path('empresa/registro/', RegistroEmpresaApi.as_view(), name='registro-empresa'),
    path('empresa/actualizar/', EmpresaView.as_view(), name='actualizar-empresa'),

    #urls para login y logout
    #path('login/', LoginView.as_view(), name='login'),
    path("admin/auth/login/", AdminLoginView.as_view()),
    path("admin/auth/refresh/", TokenRefreshView.as_view()),
    path("admin/auth/logout/", LogoutView.as_view()),
    path("admin/auth/me/", AdminMeView.as_view()),
    path("store/auth/login/", ClienteLoginView.as_view()),
    path("store/auth/refresh/", TokenRefreshView.as_view()),

    #Urls para restablecer contraseña
    path("admin/auth/password-reset/", PasswordResetRequestView.as_view()),
    path("admin/auth/password-reset/confirm/", PasswordResetConfirmView.as_view()),
    path("admin/auth/password-reset/validate/", PasswordResetValidateView.as_view()),
    
    #Urls para permisos y roles
    path("admin/permisos/", PermisoListView.as_view()),
    path("", include(router.urls)),
    
   ]+ static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)