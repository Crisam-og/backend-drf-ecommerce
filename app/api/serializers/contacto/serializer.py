from rest_framework import serializers
from api.models.contacto.models import ContactoModel

class ContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactoModel
        fields = ('contacto_id', 'nombre', 'apellido', 'telefono', 'correo', 'mensaje', 'fecha_creacion')

    def validate_nombre(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return value

    # def validate_correo(self, value):
    #     if "@" not in value or "." not in value:
    #         raise serializers.ValidationError("El correo electrónico no es válido.")
    #     return value