from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User
from .models import Comment

class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
