from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, RegisterView, LogoutView, PerfilView,
    ListaUsuariosView, CambiarRolView,
    MiNegocioView, ListaNegociosView,
    ProductosNegocioView,
    MisPedidosView, AsignarRepartidorView, ActualizarEstadoPedidoView,
)

urlpatterns = [
    path('login/',    LoginView.as_view(),    name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/',  TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/',   LogoutView.as_view(),   name='logout'),
    path('perfil/',   PerfilView.as_view(),   name='perfil'),
    path('admin/usuarios/',              ListaUsuariosView.as_view(),  name='lista-usuarios'),
    path('admin/usuarios/<int:pk>/rol/', CambiarRolView.as_view(),     name='cambiar-rol'),
    path('negocio/',           MiNegocioView.as_view(),        name='mi-negocio'),
    path('negocios/',          ListaNegociosView.as_view(),    name='lista-negocios'),
    path('negocio/productos/', ProductosNegocioView.as_view(), name='productos-negocio'),
    path('pedidos/',                        MisPedidosView.as_view(),             name='mis-pedidos'),
    path('pedidos/<int:pk>/asignar/',       AsignarRepartidorView.as_view(),      name='asignar-repartidor'),
    path('pedidos/<int:pk>/estado/',        ActualizarEstadoPedidoView.as_view(), name='actualizar-estado'),
]