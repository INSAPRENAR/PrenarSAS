def get_total_almacen(referencia):
    """
    Obtiene el total disponible en el almacén para un producto específico según su referencia.
    """
    from api_prenar.models import Producto

    try:
        # Busca el producto en la base de datos por referencia
        producto = Producto.objects.get(id=referencia)
        return producto.warehouse_quantity_conforme  # Ajusta si el campo del almacén tiene otro nombre
    except Producto.DoesNotExist:
        return 0  # Si no existe el producto, devuelve 0