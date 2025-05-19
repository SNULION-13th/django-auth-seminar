from rest_framework import serializers

# swagger api에서 보내야하는 틀을 잡는 곳.

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
    refresh = serializers.CharField() # 리프래시 토큰을 body에 넣어서 request를 쏴야한다.
    

    
class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField() # 얘도 리프래시토큰을 body에 넣어서 쏘는거니까 CharField.

