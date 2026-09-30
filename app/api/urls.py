from django.urls import path
from django.urls import include
from django.contrib import admin
from api.views.usuario.views import RegistroClienteView, ActualizarClienteView, ObtenerClienteView, EliminarClienteView,RegistroAdminView
from api.views.login.views import LoginView
from api.views.producto.views import RegistroProductoApi, ActualizarProductoApi, ListarProductosApi, EliminarProductoApi, DetalleProductoApi, RegistroCategoriaApi, ListarCategoriasApi
from api.views.empresa.views import EmpresaView
from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('registro/cliente/', RegistroClienteView.as_view(), name='registro-cliente'),
    path('actualizar/cliente/<uuid:pk>/', ActualizarClienteView.as_view(), name='actualizar-cliente'),
    path('obtener/cliente/<uuid:pk>/', ObtenerClienteView.as_view(), name='obtener-cliente'),
    path('eliminar/cliente/<uuid:pk>/', EliminarClienteView.as_view(), name='eliminar-cliente'),
    path('registro/admin/', RegistroAdminView.as_view(), name='registro-admin'),

    path('producto/registro/', RegistroProductoApi.as_view(), name='registro-producto'),
    path('producto/actualizar/<uuid:pk>/', ActualizarProductoApi.as_view(), name='actualizar-producto'),
    path('producto/listar/', ListarProductosApi.as_view(), name='listar-productos'),
    #path('producto/buscar/', ListarProductosApi.as_view(), name='buscar-productos'),
    path('producto/eliminar/<uuid:pk>/', EliminarProductoApi.as_view(), name='eliminar-producto'),
    path('producto/detalle/<uuid:pk>/', DetalleProductoApi.as_view(), name='detalle-producto'),
    path('categoria/registro/', RegistroCategoriaApi.as_view(), name='registro-categoria'),
    path('categoria/listar/', ListarCategoriasApi.as_view(), name='listar-categorias'),

    path('empresa/', EmpresaView.as_view(), name='empresa'),
    #path('empresa/registro/', RegistroEmpresaApi.as_view(), name='registro-empresa'),
    path('empresa/actualizar/', EmpresaView.as_view(), name='actualizar-empresa'),
    
    path('login/', LoginView.as_view(), name='login'),
   ]+ static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)