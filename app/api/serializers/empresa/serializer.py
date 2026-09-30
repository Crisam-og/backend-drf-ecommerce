from rest_framework import serializers
from api.models.empresa.models import EmpresaModel
from django.db import transaction

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModel
        fields = ('nombre', 'telefono', 'correo', 'direccion', 'url_whatsapp', 'logo')

class EmpresaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModel
        fields = ('nombre', 'telefono', 'correo', 'direccion', 'url_whatsapp', 'logo')
        extra_kwargs = {
            'nombre': {'required': True},
            'telefono': {'required': True},
            'correo': {'required': True},
            'direccion': {'required': True},
            'url_whatsapp': {'required': False},
            'logo': {'required': False},
        }
    @transaction.atomic
    def create(self, validated_data):
        empresa = EmpresaModel.objects.create(**validated_data)
        return empresa
    
    # @transaction.atomic
    # def update(self, instance, validated_data):
    #     instance.nombre = validated_data.get('nombre', instance.nombre)
    #     instance.telefono = validated_data.get('telefono', instance.telefono)
    #     instance.correo = validated_data.get('correo', instance.correo)
    #     instance.direccion = validated_data.get('direccion', instance.direccion)
    #     instance.url_whatsapp = validated_data.get('url_whatsapp', instance.url_whatsapp)
    #     instance.logo = validated_data.get('logo', instance.logo)
    #     instance.save()
    #     return instance
    def validate_telefono(self, value):
        if not value.isdigit() or len(value) != 9:
            raise serializers.ValidationError("El teléfono debe contener exactamente 9 dígitos numéricos.")
        return value
    def validate_nombre(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")

        return value