from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers.login.serializer import LoginSerializer
from api.models.user.models import ClienteUsuarioModel

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            print("Usuario accedido:", user)
            # datacliente = ClienteUsuarioModel.objects.filter(user=user).first()
            # print("Datos del cliente asociado:", datacliente)
            # print("Nombre del cliente:", datacliente.user.first_name)
            # print("Apellido del cliente:", datacliente.user.last_name)
            # print("Telefono del cliente:", datacliente.telefono)
            # print("Dirección del cliente:", datacliente.direccion)
            # Aquí podrías generar un token o sesión si es necesario
            return Response({
                'message': 'Login exitoso',
                'user_id': user.user.user_id,
                'email': user.user.email,
                'tipo_usuario': user.user.tipo_usuario
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)