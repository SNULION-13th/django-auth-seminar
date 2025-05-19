from django.urls import path
from .views import SignUpView, SignInView
### 🔻 TokenRefreshView 추가 ####
from .views import SignInView, SignUpView, TokenRefreshView, LogOutView
### 🔺 이 부분만 추가 ####


app_name = 'account'
urlpatterns = [
    # CBV url path
    path("signup/", SignUpView.as_view()),
    path("signin/", SignInView.as_view()),
### 🔻 이 부분만 추가 ####
    path("refresh/", TokenRefreshView.as_view()),
### 🔺 이 부분만 추가 ####
    path("logout/", LogOutView.as_view()),
]