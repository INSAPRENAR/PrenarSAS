from django.urls import path
from .views import Register, loginView, UsersView, LogoutView

urlpatterns = [
    path('register', Register.as_view(), name='register'),
    path('login', loginView.as_view(), name='login'),
    path('home', UsersView.as_view(), name='home'),
    path('logout', LogoutView.as_view(), name='logout'),
]