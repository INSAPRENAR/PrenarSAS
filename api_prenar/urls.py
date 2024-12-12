from django.urls import path
from .views import Register, loginView, UsersView, LogoutView, ListUserView, UserView, UserDetail, ClientesView, ClienteEspecificoView

urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', loginView.as_view(), name='login'),
    path('home', UsersView.as_view(), name='home'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('listUsers', ListUserView.as_view(), name='listUsers'),
    path('user/<int:user_id>', UserView.as_view(), name='user_detail'),
    path('user/<int:user_id>/update', UserDetail.as_view(), name='user-update'),
    path('user/<int:user_id>/delete', UserDetail.as_view(), name='user-delete'),
    path('cliente', ClientesView.as_view(), name='cliente'),
    path('cliente/register', ClientesView.as_view(), name='cliente-register'),
    path('cliente/<int:cliente_id>/update', ClientesView.as_view(), name='cliente-update'),
    path('cliente/<int:cliente_id>/delete', ClientesView.as_view(), name='cliente-delete'),
    path('cliente/<int:cliente_id>/detail', ClienteEspecificoView.as_view(), name='cliente-detail'),
]