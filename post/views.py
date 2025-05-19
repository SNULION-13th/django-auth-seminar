from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import Post, Like, User
from .serializers import PostSerializer, TagSerializer
from .request_serializers import PostListRequestSerializer, PostDetailRequestSerializer
from account.models import User
from tag.models import Tag
from account.request_serializers import SignInRequestSerializer
from drf_yasg import openapi

class PostListView(APIView):
    @swagger_auto_schema(
        operation_id="게시글 목록 조회",
        operation_description="게시글 목록을 조회합니다.",
        responses={
            200: PostSerializer(many=True),
            404: "Not Found",
            400: "Bad Request",
        },
         manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)],
    )
    def get(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="게시글 생성",
        operation_description="게시글을 생성합니다.",
        request_body=PostListRequestSerializer,
        responses={201: PostSerializer, 404: "Not Found", 400: "Bad Request"},
         manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)],
    )
    def post(self, request):
        title = request.data.get("title")
        content = request.data.get("content")
        tag_contents = request.data.get("tags")
        # body에서 각 data들 쭉 다 가져오고
        
        author = request.user 
        # request에서 user를 찾아보면 자동으로 클라이언트가 보낸 토큰 정보를 긁어온대. 어떻게 되는지 자세한 정보는 잘 모르겠음.
        # 근데 어쨌든 author.is_au~ 이걸로 토큰 유효 여부를 찾을 수 있는거임.
        
        if not author.is_authenticated: # user 안에 있는 기본적인 method를 통해서 바로 가져올 수 있는거다.
            # 자동으로 된대. 뭐 그렇대 그냥
            
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        # 어쨌든 login이 제대로 안되어있으면 권한 없는 걸로 간주하여 unauthor_response 보내기.
        
        if not title or not content:
            return Response(
                {"detail": "[title, content] fields missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
				
        post = Post.objects.create(title=title, content=content, author=author)

        if tag_contents is not None:
            for tag_content in tag_contents:
                if not Tag.objects.filter(content=tag_content).exists():
                    post.tags.create(content=tag_content)
                else:
                    post.tags.add(Tag.objects.get(content=tag_content))

        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class PostDetailView(APIView):
    @swagger_auto_schema(
        operation_id="게시글 상세 조회",
        operation_description="게시글 1개의 상세 정보를 조회합니다.",
        responses={200: PostSerializer, 400: "Bad Request"},
    )
    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PostSerializer(instance=post)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="게시글 삭제",
        operation_description="게시글을 삭제합니다.",
        request_body=SignInRequestSerializer,
        responses={204: "No Content", 404: "Not Found", 400: "Bad Request"},
        manual_parameters=[openapi.Parameter('Authorization', openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)],
    )
    def delete(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except:
            return Response(
                {"detail": "Post Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        author = request.user
        if not author.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        # 얘도 똑같이 login 안되어있으면 걸리는 과정 추가. 로직 자체는 단순하다~
        # (다른 login 권한 있어야 할 수 있는 과정들에 모두 이 두 칸만 채워주면 된다. 편안.)
            
        if post.author != author:
            return Response(
                {"detail": "You are not the author of this post."},
                status=status.HTTP_403_FORBIDDEN,
            )


        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id="게시글 수정",
        operation_description="게시글을 수정합니다.",
        request_body=PostDetailRequestSerializer,
        responses={200: PostSerializer, 404: "Not Found", 400: "Bad Request"},
        manual_parameters=[openapi.Parameter('Authorization', openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)],
    )
    def put(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        author = request.user
        if not author.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
            
        if post.author != author:
            return Response(
                {"detail": "You are not the author of this post."},
                status=status.HTTP_403_FORBIDDEN,
            )


        title = request.data.get("title")
        content = request.data.get("content")
        if not title or not content:
            return Response(
                {"detail": "[title, content] fields missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.title = title
        post.content = content

        tag_contents = request.data.get("tags")
        if tag_contents is not None:
            post.tags.clear()
            for tag_content in tag_contents:
                if not Tag.objects.filter(content=tag_content).exists():
                    post.tags.create(content=tag_content)
                else:
                    post.tags.add(Tag.objects.get(content=tag_content))
        post.save()
        serializer = PostSerializer(instance=post)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LikeView(APIView):
    @swagger_auto_schema(
        operation_id="좋아요 토글",
        operation_description="좋아요를 토글합니다. 이미 좋아요가 눌려있으면 취소합니다.",
        request_body=SignInRequestSerializer,
        responses={200: PostSerializer, 404: "Not Found", 400: "Bad Request"},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)],
    )
    def post(self, request, post_id):
        ### 1 ###
        try:
            post = Post.objects.get(id=post_id)
        except:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )
        author = request.user
        if not request.user.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )

        ### 3 ###
        is_liked = post.like_set.filter(user=author).count() > 0

        ### 4 ###
        if is_liked == True:
            post.like_set.get(user=author).delete()
            print("좋아요 취소")
        else:
            Like.objects.create(user=author, post=post)
            print("좋아요 누름")

        serializer = PostSerializer(instance=post)
        return Response(serializer.data, status=status.HTTP_200_OK)
