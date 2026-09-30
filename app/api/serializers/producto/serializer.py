from rest_framework import serializers
import re
from api.models.producto.models import ProductoModel, CategoriaModel
from django.db import transaction

class CategoriaSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = CategoriaModel
        fields = ('categoria_id', 'nombre', 'descripcion', 'product_count')


class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    #cant_productos = serializers.IntegerField(read_only=True)
    #nombre = serializers.CharField()
    # print("Serializer Categoria cargado:", categoria.data.pop('name', None))
    class Meta:
        model = ProductoModel
        fields = ('producto_id','categoria','nombre', 'descripcion', 'precio', 'stock', 'peso', 'imagen', 'imagen_url', 'fecha_creacion')

class RegistroProductoSerializer(serializers.ModelSerializer):
    #categoria = CategoriaSerializer()
    class Meta:
        model = ProductoModel
        fields = ('producto_id', 'categoria', 'nombre', 'descripcion', 'precio', 'stock', 'peso', 'imagen', 'imagen_url')

    def validate_nombre(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")

        # if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', value):
        #     raise serializers.ValidationError("El nombre solo debe contener letras.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        producto = ProductoModel.objects.create(**validated_data)
        return producto
        # categoria_data = validated_data.pop('categoria')
        # categoria = CategoriaModel.objects.get(categoria_id=categoria_data['categoria_id'])
        # producto = ProductoModel.objects.create(categoria=categoria, **validated_data)
        # return producto
class ActualizarProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoModel
        fields = ('categoria', 'nombre', 'descripcion', 'precio', 'stock', 'peso', 'imagen_url')
    @transaction.atomic
    def update(self, instance, validated_data):
        instance.categoria = validated_data.get('categoria', instance.categoria)
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.precio = validated_data.get('precio', instance.precio)
        instance.stock = validated_data.get('stock', instance.stock)
        instance.peso = validated_data.get('peso', instance.peso)
        instance.imagen_url = validated_data.get('imagen_url', instance.imagen_url)
        instance.save()
        return instance
    
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
    # Validaciones adicionales para precio, stock y peso si es necesario
    # def validate_precio(self, value):
    #     if value < 0:
    #         raise serializers.ValidationError("El precio no puede ser negativo.")
    #     return value
    # def validate_stock(self, value):
    #     if value < 0:
    #         raise serializers.ValidationError("El stock no puede ser negativo.")
    #     return value
    # def validate_peso(self, value):
    #     if value < 0:
    #         raise serializers.ValidationError("El peso no puede ser negativo.")
    #     return value