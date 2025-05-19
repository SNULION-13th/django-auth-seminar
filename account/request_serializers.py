from rest_framework import serializers

class SignUpRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    username = serializers.CharField()
    college = serializers.CharField()
    major = serializers.CharField()


class SignInRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class LogoutRequestSerializer(serializers.Serializer):
    refresh=serializers.CharField(
        help_text="회원가입/로그인 시 발급받은 refresh token",
        required=True
    )
