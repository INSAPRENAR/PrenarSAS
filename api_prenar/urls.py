from django.urls import path
from .views import Register, loginView, UsersView, LogoutView, ListUserView, UserView, UserDetail

urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', loginView.as_view(), name='login'),
    path('home', UsersView.as_view(), name='home'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('listUsers', ListUserView.as_view(), name='listUsers'),
    path('user/<int:user_id>', UserView.as_view(), name='user_detail'),
    path('user/<int:user_id>/update', UserDetail.as_view(), name='user-update'),
    path('user/<int:user_id>/delete', UserDetail.as_view(), name='user-delete'),
]