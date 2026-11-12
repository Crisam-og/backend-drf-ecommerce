from rest_framework import serializers
import re
from api.models.producto.models import CategoriaModel
from django.db import transaction

class CategoriaSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = CategoriaModel
        fields = ('categoria_id', 'nombre', 'descripcion', 'product_count')
class RegistroCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaModel
        fields = ('categoria_id', 'nombre', 'descripcion')
    
    def validate_nombre(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', value):
            raise serializers.ValidationError("El nombre solo debe contener letras.")
        return value
    @transaction.atomic
    def create(self, validated_data):
        categoria = CategoriaModel.objects.create(**validated_data)
        return categoria
class ActualizarCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaModel
        fields = ('nombre', 'descripcion')
    @transaction.atomic
    def update(self, instance, validated_data):
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.save()
        return instance