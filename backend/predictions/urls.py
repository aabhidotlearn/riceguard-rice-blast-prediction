from django.urls import path
from .views import RegisterView, LoginView, LogoutView, MeView, PredictionListCreateView, DashboardView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("predictions/", PredictionListCreateView.as_view()),
    path("dashboard/", DashboardView.as_view()),
]
