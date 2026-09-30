from rest_framework import serializers
from api.models.cliente.models import ClienteModel
import re

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClienteModel
        fields = ('cliente_id', 'nombre', 'logo', 'descripcion', 'sitio_web')

    def validate_nombre(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', value):
            raise serializers.ValidationError("El nombre solo debe contener letras.")
        return value