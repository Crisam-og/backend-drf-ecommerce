import re
from rest_framework import serializers as s
from api.models.entradas.models import EntradaModel, EntradaDetalleModel
from api.models.producto.models import ProductoModel, ProductoPresentacionModel
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from collections import defaultdict

class EntradaDetalleSerializer(s.ModelSerializer):
    producto_nombre = s.CharField(source="producto.nombre", read_only=True)
    presentacion = s.PrimaryKeyRelatedField(
        queryset=ProductoPresentacionModel.objects.select_related("producto")
    )

    class Meta:
        model = EntradaDetalleModel
        fields = (
            "detalle_id", "presentacion", "producto", "producto_nombre",
            "nombre_presentacion", "unidades_por_presentacion",
            "fecha_vencimiento", "cantidad", "costo_unitario", "subtotal",
        )
        read_only_fields = (
            "producto", "nombre_presentacion", "unidades_por_presentacion", "subtotal",
        )

    def validate_cantidad(self, value):
        if value < 1:
            raise s.ValidationError("La cantidad debe ser al menos 1.")
        return value

    def validate_costo_unitario(self, value):
        if value <= 0:
            raise s.ValidationError("El costo unitario debe ser mayor a 0.")
        return value

    def validate_fecha_vencimiento(self, value):
        if value <= timezone.localdate():
            raise s.ValidationError("La fecha de vencimiento debe ser posterior a hoy.")
        return value

    def validate_presentacion(self, value):
        if not value.activo or not value.producto.activo:
            raise s.ValidationError(
                f"'{value.producto.nombre} - {value.nombre}' no está disponible para ingresar."
            )
        return value


class EntradaSerializer(s.ModelSerializer):
    detalles = EntradaDetalleSerializer(many=True)
    usuario = s.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EntradaModel
        fields = [
            "entrada_id", "usuario", "fecha_ingreso", "fecha_emision",
            "tipo_comprobante", "numero_comprobante", "proveedor", "ruc",
            "subtotal_gravado", "igv", "percepcion", "monto_total",
            "imagen_comprobante", "observaciones", "detalles",
        ]
        read_only_fields = [
            "entrada_id", "usuario", "fecha_ingreso", "subtotal_gravado",
            "igv", "monto_total", "imagen_comprobante",
        ]

    def validate(self, attrs):
        if not re.fullmatch(r"\d{11}", attrs.get("ruc", "")):
            raise s.ValidationError({"ruc": "El RUC debe tener 11 dígitos numéricos."})

        if not attrs.get("detalles"):
            raise s.ValidationError({"detalles": "Agrega al menos un producto."})

        if EntradaModel.objects.filter(
            ruc=attrs["ruc"], numero_comprobante=attrs["numero_comprobante"]
        ).exists():
            raise s.ValidationError(
                {"numero_comprobante": "Esta factura ya fue registrada para ese proveedor."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        validated_data["usuario"] = self.context["request"].user
        percepcion = validated_data.pop("percepcion", Decimal("0.00"))

        # Unidades sueltas a sumar por producto
        unidades_ingresadas = defaultdict(int)
        for d in detalles_data:
            pres = d["presentacion"]
            unidades_ingresadas[pres.producto_id] += d["cantidad"] * pres.unidades_por_presentacion

        productos = {
            p.pk: p
            for p in ProductoModel.objects.select_for_update()
            .filter(pk__in=unidades_ingresadas.keys()).order_by("pk")
        }

        subtotal_general = sum(
            (d["costo_unitario"] * d["cantidad"] for d in detalles_data), Decimal("0.00")
        )
        igv = (subtotal_general * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        entrada = EntradaModel.objects.create(
            **validated_data,
            percepcion=percepcion,
            subtotal_gravado=subtotal_general,
            igv=igv,
            monto_total=subtotal_general + igv + percepcion,
        )

        EntradaDetalleModel.objects.bulk_create([
            EntradaDetalleModel(
                entrada=entrada,
                producto=productos[d["presentacion"].producto_id],
                presentacion=d["presentacion"],
                nombre_presentacion=d["presentacion"].nombre,
                unidades_por_presentacion=d["presentacion"].unidades_por_presentacion,
                fecha_vencimiento=d["fecha_vencimiento"],
                cantidad=d["cantidad"],
                costo_unitario=d["costo_unitario"],
                subtotal=d["costo_unitario"] * d["cantidad"],
            )
            for d in detalles_data
        ])

        for producto_id, unidades in unidades_ingresadas.items():
            producto = productos[producto_id]
            producto.stock += unidades
            producto.save(update_fields=["stock"])

        return entrada
