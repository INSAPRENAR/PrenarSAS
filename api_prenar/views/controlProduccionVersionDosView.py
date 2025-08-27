from collections import defaultdict
from django.db.models.functions import Coalesce
from django.db.models import IntegerField, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Producto, Inventario  # ajusta import según tu app

class PedidosProduccionView(APIView):
    def get(self, request):
        date_from = request.query_params.get("from")
        date_to   = request.query_params.get("to")

        # 1) Pedidos
        qs = Pedido.objects.select_related("id_client").only(
            "id", "order_date", "delivery_date", "order_code", "id_client", "products"
        )
        if date_from:
            qs = qs.filter(order_date__gte=date_from)
        if date_to:
            qs = qs.filter(order_date__lte=date_to)

        # 2) Referencias usadas (base)
        used_refs = set()
        for p in qs:
            for item in (p.products or []):
                try:
                    used_refs.add(int(item.get("referencia")))
                except (TypeError, ValueError):
                    pass

        if not used_refs:
            rows = [{
                "pedido_id": p.id,
                "order_date": str(p.order_date) if p.order_date else None,
                "delivery_date": str(getattr(p, "delivery_date", "") or "") or None,
                "order_code": p.order_code,
                "client": {"id": getattr(p.id_client, "id", None),
                           "name": getattr(p.id_client, "name", None)},
                "by_product": {},
            } for p in qs]
            return Response({"product_columns": [], "rows": rows}, status=status.HTTP_200_OK)

        # 3) Productos (solo los usados en pedidos)
        product_columns_qs = (
            Producto.objects
            .filter(id__in=used_refs)
            .annotate(
                warehouse_quantity_conforme_coa=Coalesce("warehouse_quantity_conforme", 0, output_field=IntegerField()),
                warehouse_quantity_not_conforme_coa=Coalesce("warehouse_quantity_not_conforme", 0, output_field=IntegerField()),
            )
            .values("id", "name", "color", "warehouse_quantity_conforme", "warehouse_quantity_not_conforme")
        )
        all_products = []
        for pc in product_columns_qs:
            pc = dict(pc)
            pc["warehouse_quantity_conforme"] = pc["warehouse_quantity_conforme"] or 0
            pc["warehouse_quantity_not_conforme"] = pc["warehouse_quantity_not_conforme"] or 0
            all_products.append(pc)
        all_products.sort(key=lambda x: (x["name"] or "", x["color"] or "", str(x["id"])))
        all_ids = [int(p["id"]) for p in all_products]
        all_id_set = set(all_ids)

        # 4) Construir filas "raw" (aplicando control y restas de inventario)
        raw_rows = []
        for p in qs:
            by_product = {str(pid): 0 for pid in all_ids}
            all_controlled = True

            # cantidades del pedido (si control=True, no se suma)
            for item in (p.products or []):
                ref = item.get("referencia")
                qty = item.get("cantidad_unidades", item.get("cantidad", 0))
                try:
                    ref_int = int(ref)
                    qty_int = int(qty or 0)
                except (TypeError, ValueError):
                    continue
                if ref_int not in all_id_set:
                    continue
                if bool(item.get("control", False)):
                    continue
                if qty_int > 0:
                    by_product[str(ref_int)] += qty_int
                    all_controlled = False

            if all_controlled:
                # nada pendiente en este pedido
                continue

            # restar producción (category=1). Si quieres sólo conforme, agrega inventory_type=1
            inv_rows = (
                Inventario.objects
                .filter(id_pedido=p.id, categori=1)
                .values("id_producto")
                .annotate(total_production=Sum("production"))
            )
            for inv in inv_rows:
                k = str(int(inv["id_producto"]))
                prod_sum = int(inv["total_production"] or 0)
                if k in by_product:
                    by_product[k] = by_product[k] - prod_sum
                    # opcional: no negativos -> by_product[k] = max(by_product[k], 0)

            raw_rows.append({
                "pedido_id": p.id,
                "order_date": str(p.order_date) if p.order_date else None,
                "delivery_date": str(getattr(p, "delivery_date", "") or "") or None,
                "order_code": p.order_code,
                "client": {"id": getattr(p.id_client, "id", None),
                           "name": getattr(p.id_client, "name", None)},
                "by_product": by_product,
            })

        # 5) Quedarse SOLO con columnas (productos) que tengan pendiente > 0 en alguna fila
        pending_ref_set = set()
        for row in raw_rows:
            for pid_str, val in row["by_product"].items():
                try:
                    if int(val) > 0:
                        pending_ref_set.add(int(pid_str))
                except (TypeError, ValueError):
                    pass

        final_product_columns = [pc for pc in all_products if int(pc["id"]) in pending_ref_set]
        final_ids = {int(pc["id"]) for pc in final_product_columns}

        # 6) Recortar cada fila a esas columnas; opcional: eliminar filas que queden en 0
        final_rows = []
        for row in raw_rows:
            filtered = {k: v for k, v in row["by_product"].items() if int(k) in final_ids}
            # si tras recortar quedó todo <= 0, puedes omitir la fila
            if not any(int(filtered.get(k, 0) or 0) > 0 for k in filtered):
                continue
            r = dict(row)
            r["by_product"] = filtered
            final_rows.append(r)

        data = {
            "product_columns": final_product_columns,  # ← sólo productos presentes con pendiente
            "rows": final_rows,                         # ← filas recortadas a esas columnas
        }
        return Response(data, status=status.HTTP_200_OK)