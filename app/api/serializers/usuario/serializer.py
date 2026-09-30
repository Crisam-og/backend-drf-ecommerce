from rest_framework import serializers
from api.models.user.models import UsuarioModel, ClienteUsuarioModel, AdministradorModel
from django.db import transaction

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = UsuarioModel
        fields = ('user_id', 'email', 'tipo_usuario', 'first_name', 'last_name', 'password')
        #read_only_fields = ('user_id', 'tipo_usuario')  # No permitir modificar desde el serializer anidado
        extra_kwargs = {
            'password': {'write_only': True}
        }
class RegistroClienteSerializer(serializers.ModelSerializer):
    user = UsuarioSerializer()
    
    class Meta:
        model = ClienteUsuarioModel
        fields = ('user', 'direccion', 'telefono')

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        
        # Usar create_user en lugar de crear manualmente
        user = UsuarioModel(
            email=user_data['email'],
            password=user_data.get('password'),
            tipo_usuario='cliente',
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )
        user.set_password(user_data.get('password'))
        user.save()
        
        cliente = ClienteUsuarioModel.objects.create(
            user=user,
            direccion=validated_data.get('direccion'),
            telefono=validated_data.get('telefono')  # Resto de campos (direccion, telefono)
        )
        
        return cliente
    
class ActualizarClienteSerializer(serializers.ModelSerializer):
    user = UsuarioSerializer()
    
    class Meta:
        model = ClienteUsuarioModel
        fields = ('user', 'direccion', 'telefono')
    
    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Obtener el objeto usuario de la relación OneToOne
        user = instance.user  # ← CORRECCIÓN AQUÍ
        
        # Actualizar campos del usuario
        for attr, value in user_data.items():
            if attr == 'password':
                user.set_password(value)
            else:
                setattr(user, attr, value)
        user.save()
        
        # Actualizar campos del cliente
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance
   
    
class RegistroAdminSerializer(serializers.ModelSerializer):
    user = UsuarioSerializer()
    
    class Meta:
        model = AdministradorModel
        fields = ('user', 'departamento')
    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        
        user = UsuarioModel(
            email=user_data['email'],
            password=user_data.get('password'),
            tipo_usuario='admin',
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_staff=True
        )
        user.set_password(user_data.get('password'))
        user.save()
        admin = AdministradorModel.objects.create(
            user=user,
            **validated_data  # departamento
        )
        
        return admin
    
