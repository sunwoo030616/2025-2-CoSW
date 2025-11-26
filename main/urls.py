from django.urls import path
from .views import RegisterView, LoginView
from .views import ping

urlpatterns = [
    path("api/ping/", ping),
    path("auth/register", RegisterView.as_view(), name="register"),
    path("auth/login", LoginView.as_view(), name="login"),
]
