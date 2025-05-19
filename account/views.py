from django.contrib.auth.models import User
from django.contrib import auth
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from account.request_serializers import SignInRequestSerializer, SignUpRequestSerializer, TokenRefreshRequestSerializer, LogoutRequestSerializer

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .serializers import (
    UserSerializer,
    UserProfileSerializer,
)
from .models import UserProfile

from rest_framework_simplejwt.tokens import RefreshToken #추가

def set_token_on_response_cookie(user, status_code):
    token = RefreshToken.for_user(user)
    user_profile = UserProfile.objects.get(user=user)
    serialized_data = UserProfileSerializer(user_profile).data
    res = Response(serialized_data, status=status_code)
    res.set_cookie("refresh_token", value=str(token), httponly=True)
    res.set_cookie("access_token", value=str(token.access_token), httponly=True)
    return res
class SignUpView(APIView):
    @swagger_auto_schema(
          operation_id="회원가입",
          operation_description="회원가입을 진행합니다.",
          request_body=SignUpRequestSerializer,
          responses={201: UserProfileSerializer, 400: "Bad Request"},
      )
    def post(self, request):
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid(raise_exception=True):
            user = user_serializer.save()
            user.set_password(user.password)
            user.save()

        college = request.data.get("college")
        major = request.data.get("major")

        user_profile = UserProfile.objects.create(
            user=user, college=college, major=major
        )
### 🔻 이 부분만 변경 ####
        return set_token_on_response_cookie(user, status_code=status.HTTP_201_CREATED)
### 🔺 이 부분만 변경 ####
        

class SignInView(APIView):
    @swagger_auto_schema(
        operation_id="로그인",
        operation_description="로그인을 진행합니다.",
        request_body=SignInRequestSerializer,
        responses={200: UserSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if username is None or password is None:
            return Response(
                {"message": "missing fields ['username', 'password'] in query_params"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                return Response(
                    {"message": "Password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
### 🔻 이 부분만 변경 ####
            return set_token_on_response_cookie(user, status_code=status.HTTP_200_OK)
### 🔺 이 부분만 변경 ####

        except User.DoesNotExist:
            return Response(
                {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


#----------------------------------------#


class TokenRefreshView(APIView):
    @swagger_auto_schema(
        operation_id="토큰 재발급",
        operation_description="access 토큰을 재발급 받습니다.",
        request_body=TokenRefreshRequestSerializer,
        responses={200: UserProfileSerializer},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        
        #### 1
        if not refresh_token:
            return Response(
                {"detail": "no refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
        #### 2
            RefreshToken(refresh_token).verify()
        except:
            return Response(
                {"detail": "please signin again."}, status=status.HTTP_401_UNAUTHORIZED
            )
            
        #### 3
        new_access_token = str(RefreshToken(refresh_token).access_token)
        response = Response({"detail": "token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie("access_token", value=str(new_access_token), httponly=True)
        return response
    
class LogOutView(APIView):
    @swagger_auto_schema(
        operation_id="로그아웃",
        operation_description="로그아웃을 진행합니다.",
        request_body=LogoutRequestSerializer,
        responses={204: "No Content", 400: "Bad Request", 401: "Unauthorized"},
    )
    def post(self, request):
        #리프레시 토큰 전달 안한경우.
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "no refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        #일단 verify를 통해 유효한 토큰인지 확인(이미 블랙리스트에 올라가있는지도 검사.)
        try:
            RefreshToken(refresh_token).verify()
        except:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        
        #혹시나 outstanding token에 존재안할 수도 있으니 확인.
        try:
            black_token = OutstandingToken.objects.get(token=refresh_token)
            BlacklistedToken.objects.create(token=black_token)
        except OutstandingToken.DoesNotExist:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

#----------------------------------------#