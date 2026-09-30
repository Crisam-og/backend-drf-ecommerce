from rest_framework import serializers
from api.models.user.models import UsuarioModel, ClienteUsuarioModel
from django.db import transaction
from django.shortcuts import get_object_or_404

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    @transaction.atomic
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            #user = get_object_or_404(UsuarioModel, email=email)
            user = UsuarioModel.objects.get(email=email)
            #datacliente = ClienteUsuarioModel.objects.get(usuario=user)
            print("Usuario encontrado en login:", user)
        except UsuarioModel.DoesNotExist:
            raise serializers.ValidationError("Usuario o contraseña incorrectos")

        if not user.check_password(password):
            raise serializers.ValidationError("Usuario o contraseña incorrectos")
        datacliente = ClienteUsuarioModel.objects.filter(user=user).first()
        print("Nombre del cliente:", datacliente.user.first_name)
        print("Apellido del cliente:", datacliente.user.last_name)
        print("Teléfono del cliente:", datacliente.telefono)
        print("Dirección del cliente:", datacliente.direccion)
        print("Email del cliente:", datacliente.user.email)
        data['user'] = datacliente
        return data