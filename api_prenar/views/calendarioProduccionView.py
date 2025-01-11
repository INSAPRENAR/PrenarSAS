from rest_framework.views import APIView
from api_prenar.serializers.calendarioSerializers import CalendarioSerializer, CalendarioTipo1Serializer, CalendarioTipo2Serializer
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Calendario

class CalendarioProduccionView(APIView):

    def post(self, request):
        try:
            serializer = CalendarioSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save() 
                return Response(
                    {"message": "Calendario registrado exitosamente.", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"message": "Error en los datos enviados.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al registrar el calendario.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, tipo=None):
        try:
            # Filtrar los calendarios según el tipo
            if tipo == 1:
                calendarios = Calendario.objects.filter(type=1)
                serializer = CalendarioTipo1Serializer(calendarios, many=True)
            elif tipo == 2:
                calendarios = Calendario.objects.filter(type=2)
                serializer = CalendarioTipo2Serializer(calendarios, many=True)
            else:
                return Response(
                    {"data": [], "message": "Tipo no válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Si encontramos calendarios para ese tipo
            if serializer.data:
                return Response(
                    {"data": serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                # Devolver data vacía con un mensaje
                return Response(
                    {"data": [], "message": "No se encontraron calendarios para este tipo."},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"data": [], "message": "Ocurrió un error al obtener los calendarios.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, calendario_id=None):
        if not calendario_id:
            return Response(
                {"message": "Debe proporcionar el ID del calendario a eliminar."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Buscar el calendario por ID
            calendario = Calendario.objects.get(id=calendario_id)
            
            # Eliminar el calendario
            calendario.delete()
            
            return Response(
                {"message": f"Calendario con ID {calendario_id} eliminado exitosamente."},
                status=status.HTTP_200_OK
            )
        except Calendario.DoesNotExist:
            return Response(
                {"message": f"No se encontró un calendario con ID {calendario_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el calendario.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )