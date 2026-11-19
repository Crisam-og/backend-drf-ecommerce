import re
from rest_framework import serializers
from api.models.producto.models import ProductoModel, ProductoPresentacionModel
from api.models.venta.models import VentaModel, VentaDetalleModel, SerieComprobanteModel
from api.views.login.views import datos_usuario
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from django.contrib.auth import get_user_model
from api.views.login.views import AdminMeView




class VentaDetalleSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    presentacion = serializers.PrimaryKeyRelatedField(
        queryset=ProductoPresentacionModel.objects.select_related("producto")
    )

    class Meta:
        model = VentaDetalleModel
        fields = (
            "ventadet_id", "presentacion", "producto", "producto_nombre",
            "nombre_presentacion", "unidades_por_presentacion",
            "precio_unitario", "cantidad", "subtotal",
        )
        read_only_fields = (
            "producto", "nombre_presentacion", "unidades_por_presentacion",
            "precio_unitario", "subtotal",
        )

    def validate_cantidad(self, value):
        if value < 1:
            raise serializers.ValidationError("La cantidad debe ser al menos 1.")
        return value

    def validate_presentacion(self, value):
        if not value.activo or not value.producto.activo:
            raise serializers.ValidationError(
                f"'{value.producto.nombre} - {value.nombre}' no está disponible para la venta."
            )
        return value


class VentaSerializer(serializers.ModelSerializer):
    detalles = VentaDetalleSerializer(many=True)
    numero_comprobante = serializers.CharField(read_only=True)
    usuario = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = VentaModel
        fields = [
            "venta_id", "usuario","tipo_comprobante", "serie", "numero", "numero_comprobante",
            "cliente", "dni_cliente", "ruc_cliente", "direccion_cliente",
            "fecha_venta", "subtotal", "igv", "total", "detalles",
        ]
        read_only_fields = [
            "venta_id", "serie", "numero", "fecha_venta", "subtotal", "igv", "total",
        ]

    def validate(self, attrs):
        tipo = attrs.get("tipo_comprobante", VentaModel.TipoComprobante.BOLETA)

        if tipo == VentaModel.TipoComprobante.FACTURA:
            if not re.fullmatch(r"\d{11}", attrs.get("ruc_cliente", "")):
                raise serializers.ValidationError(
                    {"ruc_cliente": "El RUC debe tener 11 dígitos para emitir una factura."}
                )
        else:
            if not re.fullmatch(r"\d{8}", attrs.get("dni_cliente", "")):
                raise serializers.ValidationError(
                    {"dni_cliente": "El DNI debe tener 8 dígitos para emitir una boleta."}
                )

        if not attrs.get("detalles"):
            raise serializers.ValidationError({"detalles": "Agrega al menos un producto."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        tipo = validated_data.get("tipo_comprobante", VentaModel.TipoComprobante.BOLETA)

        usuario_logueado = self.context['request'].user
        # usuario_logueado_1 = self.context['request'].user["first_nane"]
        # print(f"Usuario 1 : ", usuario_logueado_1)
        usuario_logueado_2 = self.context['request'].user.first_name
        print(f"Usuario 2 : ", usuario_logueado_2)
        validated_data['usuario'] = usuario_logueado

        # 1) Unidades base requeridas por producto (suma todas las líneas del mismo producto)
        requeridas = defaultdict(int)
        for d in detalles_data:
            pres = d["presentacion"]
            requeridas[pres.producto_id] += d["cantidad"] * pres.unidades_por_presentacion

        # 2) Bloquear productos en orden fijo (evita deadlocks) y validar stock
        productos = {
            p.pk: p
            for p in ProductoModel.objects.select_for_update()
            .filter(pk__in=requeridas.keys()).order_by("pk")
        }
        for producto_id, unidades in requeridas.items():
            producto = productos[producto_id]
            if unidades > producto.stock:
                raise serializers.ValidationError(
                    {"detalles": f"Stock insuficiente para '{producto.nombre}'. "
                                 f"Disponible: {producto.stock} unidades, "
                                 f"solicitado: {unidades}."}
                )

        # 3) Correlativo y cabecera (si algo falla, el rollback también lo deshace)
        serie, numero = SerieComprobanteModel.siguiente(tipo)
        venta = VentaModel.objects.create(
            **validated_data,
            serie=serie, numero=numero,
            subtotal=Decimal("0.00"), igv=Decimal("0.00"), total=Decimal("0.00"),
        )

        # 4) Detalles con precio tomado del servidor (nunca del cliente)
        subtotal_general = Decimal("0.00")
        for d in detalles_data:
            pres = d["presentacion"]
            cantidad = d["cantidad"]
            subtotal = pres.precio * cantidad
            VentaDetalleModel.objects.create(
                venta=venta,
                producto=productos[pres.producto_id],
                presentacion=pres,
                nombre_presentacion=pres.nombre,
                unidades_por_presentacion=pres.unidades_por_presentacion,
                precio_unitario=pres.precio,
                cantidad=cantidad,
                subtotal=subtotal,
            )
            subtotal_general += subtotal

        # 5) Descontar stock una sola vez por producto
        for producto_id, unidades in requeridas.items():
            producto = productos[producto_id]
            producto.stock -= unidades
            producto.save(update_fields=["stock"])

        igv = (subtotal_general * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        venta.subtotal = subtotal_general
        venta.igv = igv
        venta.total = subtotal_general + igv
        venta.save()
        return venta