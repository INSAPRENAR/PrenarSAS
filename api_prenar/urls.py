from django.urls import path
from .views import Register, loginView, UsersView, LogoutView, ListUserView

urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', loginView.as_view(), name='login'),
    path('home', UsersView.as_view(), name='home'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('listUsers', ListUserView.as_view(), name='listUsers'),
]