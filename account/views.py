from django.contrib.auth.models import User
from django.contrib import auth
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from account.request_serializers import SignInRequestSerializer, SignUpRequestSerializer,TokenRefreshRequestSerializer

from .serializers import (
    UserSerializer,
    UserProfileSerializer,
)
from .models import UserProfile

### 🔻 이 부분만 추가 ####
'''
def generate_token_in_serialized_data(user, user_profile):
    token = RefreshToken.for_user(user)
    refresh_token, access_token = str(token), str(token.access_token)
    serialized_data = UserProfileSerializer(user_profile).data
    serialized_data["token"] = {"access": access_token, "refresh": refresh_token}
    return serialized_data
'''
### 🔺 이 부분만 추가 ####
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
        
        return set_token_on_response_cookie(user, status_code=status.HTTP_201_CREATED)


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
        operation_description="사용자의 refresh token을 blacklist에 추가 후 폐기",
        request_body=TokenRefreshRequestSerializer,
        responses={204: "No content", 401: "Unauthorized", 400: "Bad Request"},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def post(self, request): #상태 변화가 나타나기 때문에 post
        author = request.user #access token이 header에 있으면, token decode를 통해 user를 가져옴
        if not author.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        '''
        serializer = TokenRefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        '''
        refresh_token = request.data.get("refresh") 
        try:
            token_obj = RefreshToken(refresh_token) #RefreshToken:입력받은 token decoding
            #"user_id":디코딩된 refresh_token에 포함된 속성
            
            if int(token_obj["user_id"]) != request.user.id:
                print("🔐 access user:", request.user.id)
                print("🔐 refresh token user:", token_obj['user_id'])
                return Response({"detail":"Token does not match logged-in user"},status=403)
        
        except TokenError:
            return Response({"detail":"Invalid token"},status =400)   
        try:
            token_obj.blacklist()
            return Response(status=204)
        except AttributeError:
            return Response({"detail": "Token blacklisting not enabled"}, status=500)
        