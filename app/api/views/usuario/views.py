from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers.usuario.serializer import RegistroClienteSerializer, RegistroAdminSerializer, ActualizarClienteSerializer
from api.models.user.models import ClienteUsuarioModel, UsuarioModel
from django.shortcuts import get_object_or_404

class RegistroClienteView(APIView):
    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActualizarClienteView(APIView):
    def put(self, request, pk):
        try:
            # Obtener el usuario
            user = get_object_or_404(UsuarioModel, user_id=pk)
            print("Usuario encontrado:", user)
            # Obtener el cliente asociado
            cliente = ClienteUsuarioModel.objects.get(user=user)
            
        except ClienteUsuarioModel.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Pasar la instancia de ClienteUsuarioModel, no UsuarioModel
        serializer = ActualizarClienteSerializer(cliente, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ObtenerClienteView(APIView):
    def get(self, request, pk):
        try:
            # Obtener el usuario
            user = get_object_or_404(UsuarioModel, user_id=pk)
            print("Usuario encontrado:", user)
            # Obtener el cliente asociado
            cliente = ClienteUsuarioModel.objects.get(user=user)
        except ClienteUsuarioModel.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ActualizarClienteSerializer(cliente)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EliminarClienteView(APIView):
    def delete(self, request, pk):
        try:
            # Obtener el usuario
            user = get_object_or_404(UsuarioModel, user_id=pk)
            print("Usuario encontrado:", user)
            # Obtener el cliente asociado
            cliente = ClienteUsuarioModel.objects.get(user=user)
        except ClienteUsuarioModel.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        cliente.delete()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RegistroAdminView(APIView):
    def post(self, request):
        serializer = RegistroAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)