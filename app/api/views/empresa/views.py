from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models.empresa.models import EmpresaModel
from api.serializers.empresa.serializer import EmpresaSerializer, EmpresaCreateUpdateSerializer


class EmpresaView(APIView):
    def get(self, request):
        empresa = EmpresaModel.get_solo()
        serializer = EmpresaSerializer(empresa)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        empresa = EmpresaModel.get_solo()  # crea si no existe, obtiene si ya existe
        serializer = EmpresaCreateUpdateSerializer(empresa, data=request.data, partial=True)
        if serializer.is_valid():
            empresa = serializer.save()
            return Response(EmpresaSerializer(empresa).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class RegistroEmpresaApi(APIView):
#     def post(self, request):
#         if EmpresaModel.objects.exists():
#             return Response({"error": "Ya existe una empresa registrada."}, status=status.HTTP_400_BAD_REQUEST)
        
#         serializer = EmpresaCreateUpdateSerializer(data=request.data)
#         if serializer.is_valid():
#             empresa = serializer.save()
#             return Response(EmpresaSerializer(empresa).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class ActualizarEmpresaApi(APIView):
#     def put(self, request):
#         empresa = EmpresaModel.get_solo()
#         serializer = EmpresaCreateUpdateSerializer(empresa, data=request.data, partial=True)
#         if serializer.is_valid():
#             empresa = serializer.save()
#             return Response(EmpresaSerializer(empresa).data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# class EmpresaView(APIView):
#     """
#     GET: Obtiene los datos de la empresa (crea instancia vacía si no existe)
#     PUT/PATCH: Crea o actualiza la empresa
#     """
    
#     def get(self, request):
#         empresa = Empresa.get_solo()
#         serializer = EmpresaSerializer(empresa)
#         return Response(serializer.data)
    
#     def put(self, request):
#         empresa = Empresa.get_solo()  # Siempre obtiene o crea la instancia
#         serializer = EmpresaSerializer(empresa, data=request.data, partial=False)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     def patch(self, request):
#         empresa = Empresa.get_solo()
#         serializer = EmpresaSerializer(empresa, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)