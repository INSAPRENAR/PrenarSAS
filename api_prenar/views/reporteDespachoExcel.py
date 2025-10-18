from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.db.models import Q
from decimal import Decimal

import openpyxl
from openpyxl.styles import Font, Border, Side
from openpyxl.utils import get_column_letter

from api_prenar.models import CalendarioDespacho
from api_prenar.serializers.calendarioDespachoSerializers import CalendarioListSerializer
# ^ ajusta el import del serializer a tu ruta real
#   (en tu mensaje el nombre era CalendarioListSerializer; deja el path correcto)

class DownloadCronogramaDespachoView(APIView):
    """
    GET /reporte/cronograma/produccion/download/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

    Genera un Excel con el mismo diseño que la tabla del front (sin columna "Acciones").
    Columnas:
    - Fecha Inicio | Fecha Fin | Fecha | Pedido | Nombre | Color |
      Vr. unit. | Programación | Total prog. | Producción | Falto | Observación
    """

    def get(self, request):
        try:
            # 1) Filtros (front envía start_date y end_date)
            start_date = request.query_params.get("start_date", None)
            end_date = request.query_params.get("end_date", None)

            filters = Q()
            if start_date and end_date:
                filters &= Q(start_date__gte=start_date, start_date__lte=end_date)
            elif start_date:
                filters &= Q(start_date__gte=start_date)
            elif end_date:
                filters &= Q(start_date__lte=end_date)

            qs = CalendarioDespacho.objects.filter(filters).order_by("-start_date")
            if not qs.exists():
                return Response(
                    {"message": "No se encontraron calendarios de despacho con los filtros especificados."},
                    status=status.HTTP_200_OK
                )

            # 2) Serializar
            ser = CalendarioListSerializer(qs, many=True)
            calendarios = ser.data  # lista de dicts

            # 3) Crear workbook y hoja
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Cronograma Despacho"

            # 4) Encabezados (como la tabla del front, sin "Acciones")
            headers = [
                "Fecha Inicio",
                "Fecha Fin",
                "Fecha",
                "Pedido",
                "Nombre Producto",
                "Color",
                "Vr. unit.",
                "Programación",
                "Total prog.",
                "Despacho",
                "Falto",
                "Observación",
            ]
            ws.append(headers)
            # Negrita a encabezados
            for cell in ws[1]:
                cell.font = Font(bold=True)

            # 5) Llenar filas
            current_row = 2
            for cal in calendarios:
                start_date_val = cal.get("start_date", "")
                end_date_val = cal.get("end_date", "")
                observation_val = (cal.get("observation") or "").strip()

                items = cal.get("dispatch") or []  # lista de dicts (JSONField)
                if not isinstance(items, list):
                    items = []

                if len(items) == 0:
                    # Fila sin detalles de producción, pero con base del calendario
                    ws.cell(row=current_row, column=1, value=start_date_val)
                    ws.cell(row=current_row, column=2, value=end_date_val)
                    ws.cell(row=current_row, column=3, value="")  # Fecha producción
                    ws.cell(row=current_row, column=4, value="")  # Pedido
                    ws.cell(row=current_row, column=5, value="")  # Nombre
                    ws.cell(row=current_row, column=6, value="")  # Color
                    ws.cell(row=current_row, column=7, value=0)   # Vr. unit.
                    ws.cell(row=current_row, column=8, value=0)   # Programación
                    ws.cell(row=current_row, column=9, value=0)   # Total prog.
                    ws.cell(row=current_row, column=10, value=0)  # Producción
                    ws.cell(row=current_row, column=11, value=0)  # Falto
                    ws.cell(row=current_row, column=12, value=observation_val)
                    current_row += 1
                    continue

                # Con detalles
                for it in items:
                    # Tomar valores robustamente (pueden venir como str/Decimal/etc.)
                    fecha_prod = it.get("fecha", "")
                    name_pedido = (it.get("name_pedido") or "").strip()
                    pedido_show = name_pedido if name_pedido else "Sin Pedido"
                    name = it.get("name", "")
                    color = it.get("color", "")

                    def to_number(x):
                        # convierte str/Decimal/None a float (o 0)
                        if isinstance(x, Decimal):
                            return float(x)
                        try:
                            return float(x)
                        except Exception:
                            return 0.0

                    vr_unit = to_number(it.get("valor_unitario", 0))
                    prog = int(it.get("programacion_cantidad", 0) or 0)
                    total_prog = to_number(it.get("total_programacion", 0))
                    prod = int(it.get("produccion", 0) or 0)
                    saldo = int(it.get("saldo", 0) or 0)

                    ws.cell(row=current_row, column=1, value=start_date_val)
                    ws.cell(row=current_row, column=2, value=end_date_val)
                    ws.cell(row=current_row, column=3, value=fecha_prod)
                    ws.cell(row=current_row, column=4, value=pedido_show)
                    ws.cell(row=current_row, column=5, value=name)
                    ws.cell(row=current_row, column=6, value=color)
                    ws.cell(row=current_row, column=7, value=vr_unit)
                    ws.cell(row=current_row, column=8, value=prog)
                    ws.cell(row=current_row, column=9, value=total_prog)
                    ws.cell(row=current_row, column=10, value=prod)
                    ws.cell(row=current_row, column=11, value=saldo)
                    ws.cell(row=current_row, column=12, value=observation_val)

                    current_row += 1

            # 6) Ajustes de ancho de columna y bordes finos
            # Anchos sugeridos por legibilidad (puedes ajustarlos)
            widths = [15, 15, 12, 11, 28, 18, 14, 14, 14, 12, 10, 32]
            for idx, width in enumerate(widths, start=1):
                col_letter = get_column_letter(idx)
                ws.column_dimensions[col_letter].width = width

            thin = Border(left=Side(style="thin"),
                          right=Side(style="thin"),
                          top=Side(style="thin"),
                          bottom=Side(style="thin"))
            for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                                    min_col=1, max_col=ws.max_column):
                for cell in row:
                    cell.border = thin

            # 7) Respuesta como archivo
            filename = "Cronograma_Despacho.xlsx"
            if start_date and end_date:
                filename = f"Cronograma_Despacho_{start_date}_a_{end_date}.xlsx"
            elif start_date:
                filename = f"Cronograma_Despacho_desde_{start_date}.xlsx"
            elif end_date:
                filename = f"Cronograma_Despacho_hasta_{end_date}.xlsx"

            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            wb.save(response)
            return response

        except Exception as e:
            return Response(
                {"message": "Error al generar el archivo.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )