from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User
from .models import Comment

from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    응답 전용 Serializer
    author 정보를 객체로 내려주도록 커스터마이징
    """

    author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "created_at")

    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "username": obj.author.username,
            "email": obj.author.email,
        }
