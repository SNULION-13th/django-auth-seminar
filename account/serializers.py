from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User
from .models import UserProfile


class UserIdUsernameSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password", "email"]


class UserProfileSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    # Python 클래스 문법 상, 클래스 안에서 변수명 = 값을 쓰면 그게 그 클래스의 속성(필드)이 됨
    # 그래서 user 변수명을 재정의(override) 해주는 느낌이다.
    
    class Meta:
        model = UserProfile
        fields = "__all__"