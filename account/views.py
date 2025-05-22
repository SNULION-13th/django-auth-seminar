from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from account.request_serializers import (
    SignInRequestSerializer,
    SignUpRequestSerializer,
    TokenRefreshRequestSerializer,
)

from .serializers import UserSerializer, UserProfileSerializer
from .models import UserProfile


class SignUpView(APIView):
    @swagger_auto_schema(
        operation_id="회원가입",
        operation_description="회원가입을 진행합니다.",
        request_body=SignUpRequestSerializer,
        responses={201: UserProfileSerializer, 400: "Bad Request"},
    )
    def post(self, request):
        college=request.data.get('college')
        major=request.data.get('major')

        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid(raise_exception=True):
            user = user_serializer.save()
            user.set_password(user.password)
            user.save()
            
        user_profile = UserProfile.objects.create(
            user=user,
            college=college,
            major=major
        )
### 🔻 이 부분만 추가 ####
        return set_token_on_response_cookie(user, status_code=status.HTTP_201_CREATED)
### 🔺 이 부분만 추가 ####

class SignInView(APIView):
    @swagger_auto_schema(
        operation_id="로그인",
        operation_description="로그인을 진행합니다.",
        request_body=SignInRequestSerializer,
        responses={204: "No Content", 404: "Not Found", 400: "Bad Request"},
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                return Response(
                    {"message": "Password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return set_token_on_response_cookie(user, status_code=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


def generate_token_in_serialized_data(user, user_profile):
    token = RefreshToken.for_user(user)
    user_profile_serializer = UserProfileSerializer(user_profile)
    res = Response(user_profile_serializer.data, status=status.HTTP_201_CREATED)
    res.set_cookie('refresh_token', value=str(token), httponly=True)
    res.set_cookie('access_token', value=str(token.access_token), httponly=True)
    return res

def set_token_on_response_cookie(user, status_code):
    token = RefreshToken.for_user(user)
    user_profile = UserProfile.objects.get(user=user)
    serialized_data = UserProfileSerializer(user_profile).data
    res = Response(serialized_data, status=status_code)
    res.set_cookie("refresh_token", value=str(token), httponly=True)
    res.set_cookie("access_token", value=str(token.access_token), httponly=True)
    return res



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
    
class SignOutView(APIView):
    @swagger_auto_schema(
        operation_id="로그아웃",
        operation_description="사용자를 로그아웃 시킵니다.",
        # Authorization 헤더를 명시적으로 요구
        manual_parameters=[
            openapi.Parameter(
                name='Authorization',
                in_=openapi.IN_HEADER,
                description='Bearer <access_token>',
                type=openapi.TYPE_STRING,
                required=True,
            )
    
        ],
        request_body=TokenRefreshRequestSerializer,
        responses={
            204: openapi.Response(description="No Content"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
        },
    )
    def post(self, request):
        # 1) 인증 헤더 검사
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "please signin"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2) body의 refresh 토큰 검사
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "no refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) 블랙리스트 등록
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "token is invalid or already blacklisted"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 4) 쿠키 삭제 후 204 반환
        res = Response(status=status.HTTP_204_NO_CONTENT)
        res.delete_cookie("access_token")
        res.delete_cookie("refresh_token")
        return res