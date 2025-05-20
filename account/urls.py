from django.urls import path
from .views import SignUpView, SignInView, TokenRefreshView, LogOutView


app_name = 'account'
urlpatterns = [
    # CBV url path
    path("signup/", SignUpView.as_view()),
    path("signin/", SignInView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", LogOutView.as_view()),
]