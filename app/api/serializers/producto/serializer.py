from rest_framework import serializers
import re
from api.models.producto.models import ProductoModel, ProductoPresentacionModel
from api.serializers.categoria.serializer import CategoriaSerializer
from django.db import transaction






class RegistroProductoSerializer(serializers.ModelSerializer):
    #categoria = CategoriaSerializer()
    class Meta:
        model = ProductoModel
        fields = ('producto_id','categoria','nombre', 'stock', 'descripcion', 'imagen', 'imagen_url', 'activo', )

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
    
class ActualizarProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoModel
        fields = ('categoria', 'nombre', 'stock','descripcion', 'imagen_url', 'activo')
    @transaction.atomic
    def update(self, instance, validated_data):
        instance.categoria = validated_data.get('categoria', instance.categoria)
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.stock = validated_data.get('stock', instance.stock)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.imagen_url = validated_data.get('imagen_url', instance.imagen_url)
        instance.activo = validated_data.get('activo', instance.activo)
        instance.save()
        return instance
    
class ProdPresentSerializer(serializers.ModelSerializer):
    stock_disponible = serializers.SerializerMethodField()

    class Meta:
        model = ProductoPresentacionModel
        fields = ('presentacion_id', 'nombre', 'sku', 'unidades_por_presentacion',
                  'precio', 'activo', 'stock_disponible')

    def get_stock_disponible(self, obj):
        return obj.producto.stock // obj.unidades_por_presentacion

class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    presentaciones = ProdPresentSerializer(many=True, read_only=True)

    class Meta:
        model = ProductoModel
        fields = ('producto_id', 'categoria', 'nombre', 'descripcion', 'stock',
                  'imagen', 'imagen_url', 'activo', 'fecha_creacion', 'presentaciones')

class CreateProdPresentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoPresentacionModel
        fields = (
            'presentacion_id', 'producto', 'nombre', 'sku',
            'unidades_por_presentacion', 'precio', 'activo',
        )

    def validate(self, attrs):
        # "Unidad" siempre debe equivaler a 1 unidad base
        if attrs.get('nombre', '').strip().lower() == 'unidad' \
                and attrs.get('unidades_por_presentacion') != 1:
            raise serializers.ValidationError(
                {'unidades_por_presentacion': 'Para "Unidad" debe ser 1.'}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        prod_present = ProductoPresentacionModel.objects.create(**validated_data)
        return prod_present

class UpdateProdPresentSerializer(serializers.ModelSerializer):
    class Meta:
                model = ProductoPresentacionModel
                fields = ('presentacion_id', 'producto', 'nombre', 'sku', 'unidades_por_presentacion', 'precio', 'activo')

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.producto = validated_data.get('producto', instance.producto)
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.sku = validated_data.get('sku', instance.sku)
        instance.unidades_por_presentacion = validated_data.get('unidades_por_presentacion', instance.unidades_por_presentacion)
        instance.precio = validated_data.get('precio', instance.precio)
        instance.activo = validated_data.get('activo', instance.activo)
        instance.save()
        return instance



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