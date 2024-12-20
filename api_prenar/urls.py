from django.urls import path
from .views import Register, loginView, UsersView, LogoutView, ListUserView, UserView, UserDetail, ClientesView, ClienteEspecificoView, PedidoView, PagoView, InventarioView, ProductoView, ProductoEspecificoView, DespachoView, ProductosPedidoDespachoView, ListaNumerosPedidosView

urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', loginView.as_view(), name='login'),
    path('home', UsersView.as_view(), name='home'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('listUsers', ListUserView.as_view(), name='listUsers'),
    path('user/<int:user_id>', UserView.as_view(), name='user_detail'),
    path('user/<int:user_id>/update', UserDetail.as_view(), name='user-update'),
    path('user/<int:user_id>/delete', UserDetail.as_view(), name='user-delete'),
    path('clientes', ClientesView.as_view(), name='cliente'),
    path('cliente/register', ClientesView.as_view(), name='cliente-register'),
    path('cliente/<int:cliente_id>/update', ClientesView.as_view(), name='cliente-update'),
    path('cliente/<int:cliente_id>/delete', ClientesView.as_view(), name='cliente-delete'),
    path('cliente/<int:cliente_id>/detail', ClienteEspecificoView.as_view(), name='cliente-detail'),
    path('pedido/register', PedidoView.as_view(), name='pedido-register'),
    path('pedidos/cliente/<int:cliente_id>', PedidoView.as_view(), name='listPedidos'),
    path('pedidos/pedido/<int:pedido_id>/update', PedidoView.as_view(), name='pedido-update'),
    path('pedidos/pedido/<int:pedido_id>/delete', PedidoView.as_view(), name='pedido-update'),
    path('pago/register', PagoView.as_view(), name='pago-register'),
    path('pago/<int:pago_id>/delete', PagoView.as_view(), name='pago-delete'),
    path('inventario/register', InventarioView.as_view(), name='inventario-register'),
    path('inventario/<int:inventario_id>/delete', InventarioView.as_view(), name='inventario-delete'),
    path('producto/register', ProductoView.as_view(), name='producto-register'),
    path('productos', ProductoView.as_view(), name='productos'),
    path('producto/<int:producto_id>', ProductoEspecificoView.as_view(), name='producto-detail'),
    path('productos/producto/<int:producto_id>/update', ProductoView.as_view(), name='producto-update'),
    path('producto/<int:producto_id>/delete', ProductoView.as_view(), name='producto-delete'),
    path('despacho/register', DespachoView.as_view(), name='despacho-register'),
    path('despacho/<int:despacho_id>/delete', DespachoView.as_view(), name='despacho-delete'),
    path('despacho/lista/productos/<int:pedido_id>', ProductosPedidoDespachoView.as_view(), name='lista-productos-despacho'),
    path('lista/pedidos/numero/pendientes', ListaNumerosPedidosView.as_view(), name='lista-numero-pedidos-pendientes'),
]