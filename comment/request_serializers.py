from rest_framework import serializers
from account.request_serializers import SignInRequestSerializer

class CommentListRequestSerializer(serializers.Serializer):
    author = SignInRequestSerializer(required=True)
    post = serializers.IntegerField(required=True)  # Post ID
    content = serializers.CharField(required=True, min_length=1)  # 댓글 내용

class CommentDetailRequestSerializer(serializers.Serializer):
    author = SignInRequestSerializer(required=True)
    content = serializers.CharField(required=True, min_length=1)  # 댓글 내용

