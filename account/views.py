from django.contrib.auth.models import User
from django.contrib import auth
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from account.request_serializers import SignInRequestSerializer, SignUpRequestSerializer, TokenRefreshRequestSerializer, LogoutRequestSerializer

from .serializers import (
    UserSerializer,
    UserProfileSerializer,
)
from .models import UserProfile

from rest_framework_simplejwt.tokens import RefreshToken #추가



# 로그인 같은거 할때도 JWT를 계속 발급받아야하니 재사용성을 위해서 token 만드는 함수를 따로 만들어준다.
def generate_token_in_serialized_data(user, user_profile):
    token = RefreshToken.for_user(user)
    refresh_token, access_token = str(token), str(token.access_token) # token을 발급하는 상황.
    serialized_data = UserProfileSerializer(user_profile).data
    serialized_data["token"] = {"access": access_token, "refresh": refresh_token}
    return serialized_data
# 아래 셋 쿠키 설정 이후에는 안씀. 위의 함수는 serialized_data라는 body에 토큰을 담아서 보내기 떄문에 보안상 이유로.

def set_token_on_response_cookie(user, status_code): # 쿠키도 재사용하는거.
    token = RefreshToken.for_user(user)
    user_profile = UserProfile.objects.get(user=user) # user_profile까지는 인자에 안받아서 user_profile 따로 설정정
    serialized_data = UserProfileSerializer(user_profile).data
    res = Response(serialized_data, status=status_code) # response에는 token 내용 없이 빼고
    res.set_cookie("refresh_token", value=str(token), httponly=True) # .set_cookie는 response 객체에 원래 있는 method래. 그냥 알고 사용하면 될듯.
    res.set_cookie("access_token", value=str(token.access_token), httponly=True)
    return res
# 얘가 이제 generate_token 함수 역할까지 한번에 해준다. 쿠키에 토큰을 담아서 클라이언트들에게도 보내줌


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
        
    ## 추가.
        return set_token_on_response_cookie(user, status_code=status.HTTP_201_CREATED)
    # 토큰을 '쿠키'에 담아서 보내는 과정이다. 앞에서 함수로 정의되어있음. 
    # 원래 이전 코드까지는 response body에 담아서 보냈었는데, 그러면 보안이 너무 취약하거든...
    # 그러면 이제 클라이언트는 토큰이 들어있는 쿠키를 받게되는 것이다!

class SignInView(APIView):
    @swagger_auto_schema(
        operation_id="로그인",
        operation_description="로그인을 진행합니다.",
        request_body=SignInRequestSerializer,
        responses={200: UserSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def post(self, request):
        username = request.data.get("username") # request에서 username, password 가지고 와서서
        password = request.data.get("password")
        if username is None or password is None:
            return Response(
                {"message": "missing fields ['username', 'password'] in query_params"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # username을 이용해서 user 객체를 만들고 / password를 확인해보고 / 맞다면..
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                return Response(
                    {"message": "Password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            return set_token_on_response_cookie(user, status_code=status.HTTP_200_OK)
    # signIn 했을때도 쿠키 보내준다. 이러면 로그인이 완료된 것.
    # signUp 했을 때도 토큰 담아서 쿠키를 보내주는 걸로 보아, 그때도 그냥 자동 로그인 되는 듯
    
        except User.DoesNotExist:
            return Response(
                {"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
    # 이러면 이제 클라이언트는 2개의 토큰에 대한 정보를 가지고 있는 것이다 ~
            
            
            
# 토큰 재발급 class. 
class TokenRefreshView(APIView):
    @swagger_auto_schema(
        operation_id="토큰 재발급",
        operation_description="access 토큰을 재발급 받습니다.",
        request_body=TokenRefreshRequestSerializer,
        responses={200: UserProfileSerializer},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh") # request에서 refresh 부분을 받아온다.
        
        #### 1
        if not refresh_token: # 비어있으면 오류
            return Response(
                {"detail": "no refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
        #### 2
        # 리프레시 토큰 유효한지 확인 과정. 그냥 딸깍임.
            RefreshToken(refresh_token).verify() # 리프레시 토큰까지 아예 틀렸을때. 리프레시 토큰은 하루마다 초기화되니까, 우리는 최소 하루마다는 다시 로그인을 해줘야한다.
            # 물론 명시적으로 로그아웃을 하는 기능도 필요하지. 그래서 과제에서 그걸 구현해야하는거고.
        except:
            return Response(
                {"detail": "please signin again."}, status=status.HTTP_401_UNAUTHORIZED
            )
            
        #### 3
        # 새로운 access token 발급 과정. 이것도 거의 딸깍. 이후 response의 쿠키로 쏴준다!
        new_access_token = str(RefreshToken(refresh_token).access_token)
        response = Response({"detail": "token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie("access_token", value=str(new_access_token), httponly=True)
        return response
            
            
            
# 로그아웃 클래스
# 로그아웃도 이런 토큰refresh와 비슷하게 짜면 될듯한데? 새로 class만들고, model, url 추가하고. post 요청오면 로그아웃이 되게끔. 
# (app을 새로 만들 필요는 없어보임)
class LogoutView(APIView):
    @swagger_auto_schema(
        operation_id="로그아웃",
        operation_description="refresh token을 free 시켜 로그아웃합니다.",
        request_body=LogoutRequestSerializer,
        responses={204: "No Content", 401: "Unauthorized", 400: "Bad Request" },
        manual_parameters=[openapi.Parameter('Authorization', openapi.IN_HEADER, description="Token Authentication", type=openapi.TYPE_STRING, required=True)], # 헤더에 들어가는 것, 타입은 문자열인 것들을 swagger에서 보낼 수 있도록.
    )   # required 옵션도 추가.
    def post(self, request):
        refresh_token = request.data.get("refresh") # request에서 refresh 부분을 받아온다.
        
        if not refresh_token: # 비어있으면 400 bad request 오류
            return Response(
                {"detail": "no refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        # 잘못된 refresh_token이면 401 오류
        try:
        # 리프레시 토큰 유효한지 확인 과정. 그냥 딸깍임.
            RefreshToken(refresh_token).verify() # 틀렸으면 그냥 바로 401 오류
        except:
            return Response(
                {"detail": "please signin again."}, status=status.HTTP_401_UNAUTHORIZED
            )
            
        # 마지막으로 기본적인 사항들 다 통과했으면 refresh_token을 블랙리스트에 추가하고 204 반환.
        # 반환값이 없으니 serializers.py에 추가되어야하는 정보들은 없음.
        RefreshToken(refresh_token).blacklist() # 이거 하면 바로 blacklist에 올라간다.
        
        response = Response({}, status=status.HTTP_204_NO_CONTENT) # 빈 json 리턴해야함
        response.delete_cookie("access_token") # 이거 안하면 이전에 set해놓은게 계속 그대로 유지된다.. delete 필요.
        response.delete_cookie("refresh_token")
        return response