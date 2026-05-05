from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Usuario, Rol, Negocio, Producto, Pedido, DetallePedido
from .serializers import (
    RegisterSerializer, UsuarioSerializer,
    CustomTokenObtainPairSerializer,
    NegocioSerializer, NegocioCreateSerializer,
    ProductoSerializer, PedidoSerializer,
)
from .permissions import EsAdmin, EsCliente, EsRepartidor, EsPropietarioDeNegocio, EsAdminORepartidor


# ──────────────────────────────────────────
# AUTENTICACIÓN
# ──────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Devuelve access token, refresh token y datos del usuario.
    No requiere token (es el endpoint para obtenerlo).
    """
    serializer_class   = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Crea un usuario nuevo. Por defecto se le asigna rol 'cliente'.
    No requiere token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            # Si no mandaron rol, asignamos 'cliente' por defecto
            if not usuario.rol:
                try:
                    usuario.rol = Rol.objects.get(nombre='cliente')
                    usuario.save()
                except Rol.DoesNotExist:
                    pass
            return Response(
                {'mensaje': 'Usuario registrado correctamente', 'usuario': UsuarioSerializer(usuario).data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Invalida el refresh token.
    Requiere: estar autenticado.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({'mensaje': 'Sesión cerrada correctamente'})
        except Exception:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)


class PerfilView(APIView):
    """
    GET  /api/auth/perfil/    → ver mi perfil
    PUT  /api/auth/perfil/    → editar mis datos
    Requiere: Bearer token válido.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)

    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────
# ADMINISTRACIÓN (solo admin)
# ──────────────────────────────────────────

class ListaUsuariosView(APIView):
    """
    GET /api/auth/admin/usuarios/
    Lista todos los usuarios del sistema.
    Requiere: rol admin.
    """
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        usuarios = Usuario.objects.select_related('rol').all()
        return Response(UsuarioSerializer(usuarios, many=True).data)


class CambiarRolView(APIView):
    """
    PUT /api/auth/admin/usuarios/<id>/rol/
    Cambia el rol de un usuario.
    Requiere: rol admin.
    Body: { "rol": "repartidor" }
    """
    permission_classes = [IsAuthenticated, EsAdmin]

    def put(self, request, pk):
        try:
            usuario = Usuario.objects.get(pk=pk)
            rol     = Rol.objects.get(nombre=request.data.get('rol'))
            usuario.rol = rol
            usuario.save()
            return Response({'mensaje': f'Rol actualizado a {rol.nombre}'})
        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Rol.DoesNotExist:
            return Response({'error': 'Rol inválido'}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────
# NEGOCIOS
# ──────────────────────────────────────────

class MiNegocioView(APIView):
    """
    GET  /api/auth/negocio/    → ver mi negocio
    POST /api/auth/negocio/    → registrar mi negocio
    Requiere: estar autenticado.
    Cualquier usuario puede registrar un negocio (clientes también).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return Response(NegocioSerializer(request.user.negocio).data)
        except Negocio.DoesNotExist:
            return Response({'error': 'No tienes un negocio registrado'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        if hasattr(request.user, 'negocio'):
            return Response({'error': 'Ya tienes un negocio registrado'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = NegocioCreateSerializer(data=request.data)
        if serializer.is_valid():
            negocio = serializer.save(propietario=request.user)
            return Response(NegocioSerializer(negocio).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListaNegociosView(APIView):
    """
    GET /api/auth/negocios/
    Lista todos los negocios activos.
    Requiere: estar autenticado (cualquier rol puede ver negocios).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        negocios = Negocio.objects.filter(activo=True).select_related('propietario')
        return Response(NegocioSerializer(negocios, many=True).data)


# ──────────────────────────────────────────
# PRODUCTOS
# ──────────────────────────────────────────

class ProductosNegocioView(APIView):
    """
    GET  /api/auth/negocio/productos/          → ver mis productos
    POST /api/auth/negocio/productos/          → crear producto
    Requiere: tener un negocio registrado.
    """
    permission_classes = [IsAuthenticated, EsPropietarioDeNegocio]

    def get(self, request):
        productos = Producto.objects.filter(negocio=request.user.negocio)
        return Response(ProductoSerializer(productos, many=True).data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(negocio=request.user.negocio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────
# PEDIDOS
# ──────────────────────────────────────────

class MisPedidosView(APIView):
    """
    GET /api/auth/pedidos/
    - Si es cliente:     ve sus propios pedidos.
    - Si es repartidor:  ve los pedidos asignados a él.
    - Si es admin:       ve todos los pedidos.
    Requiere: estar autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rol = request.user.rol.nombre if request.user.rol else None

        if rol == 'admin':
            pedidos = Pedido.objects.select_related('cliente', 'negocio', 'repartidor').all()
        elif rol == 'repartidor':
            pedidos = Pedido.objects.filter(repartidor=request.user)
        else:
            pedidos = Pedido.objects.filter(cliente=request.user)

        return Response(PedidoSerializer(pedidos, many=True).data)


class AsignarRepartidorView(APIView):
    """
    PUT /api/auth/pedidos/<id>/asignar/
    Asigna un repartidor a un pedido.
    Requiere: rol admin.
    Body: { "repartidor_id": 5 }
    """
    permission_classes = [IsAuthenticated, EsAdmin]

    def put(self, request, pk):
        try:
            pedido      = Pedido.objects.get(pk=pk)
            repartidor  = Usuario.objects.get(pk=request.data.get('repartidor_id'), rol__nombre='repartidor')
            pedido.repartidor = repartidor
            pedido.estado     = 'confirmado'
            pedido.save()
            return Response({'mensaje': f'Repartidor {repartidor.nombre} asignado al pedido #{pedido.id}'})
        except Pedido.DoesNotExist:
            return Response({'error': 'Pedido no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Usuario.DoesNotExist:
            return Response({'error': 'Repartidor no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ActualizarEstadoPedidoView(APIView):
    """
    PUT /api/auth/pedidos/<id>/estado/
    El repartidor actualiza el estado de su pedido asignado.
    Requiere: rol repartidor, y que el pedido le pertenezca.
    Body: { "estado": "en_camino" }
    """
    permission_classes = [IsAuthenticated, EsRepartidor]

    def put(self, request, pk):
        try:
            pedido = Pedido.objects.get(pk=pk, repartidor=request.user)
            nuevo_estado = request.data.get('estado')
            estados_validos = ['en_camino', 'entregado']
            if nuevo_estado not in estados_validos:
                return Response({'error': f'Estado inválido. Opciones: {estados_validos}'}, status=status.HTTP_400_BAD_REQUEST)
            pedido.estado = nuevo_estado
            pedido.save()
            return Response({'mensaje': f'Pedido #{pedido.id} actualizado a {nuevo_estado}'})
        except Pedido.DoesNotExist:
            return Response({'error': 'Pedido no encontrado o no te pertenece'}, status=status.HTTP_404_NOT_FOUND)
