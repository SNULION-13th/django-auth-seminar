from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Comment
from account.models import User
from account.request_serializers import SignInRequestSerializer
from .serializers import CommentSerializer
from .request_serializers import CommentListRequestSerializer, CommentDetailRequestSerializer
from post.models import Post

def get_post_or_404(post_id):
    try:
        return Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return None

class CommentView(APIView):
    @swagger_auto_schema(
        operation_id="댓글 목록 조회",
        operation_description="특정 post의 모든 comments를 반환합니다.",
        manual_parameters=[
            openapi.Parameter(
                'post',  # 파라미터 이름
                openapi.IN_QUERY,  # 쿼리 파라미터
                description="댓글을 반환할 post의 id",
                type=openapi.TYPE_INTEGER,  # 파라미터 타입
                required=True,  # 필수 여부
            )
        ],
        responses={
            200: CommentSerializer(many=True),
            404: "Post not found.",
        },
    )
    def get(self, request):
        post_id = request.query_params.get('post')
        post = get_post_or_404(post_id)
        if not post:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="댓글 생성",
        operation_description="특정 게시글에 댓글을 생성합니다.",
        request_body=CommentListRequestSerializer,
        responses={
            201: CommentSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found",
            403: "Forbidden",
        },
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        author = request.user
        post_id = request.data.get("post")
        content = request.data.get("content")

        if not post_id or not content:
            return Response(
                {"detail": "missing fields ['post', 'content']"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not Post.objects.filter(id=post_id).exists():
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        comment = Comment.objects.create(
            post_id=post_id, author=author, content=content
        )
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class CommentDetailView(APIView):
    @swagger_auto_schema(
        operation_id="댓글 수정",
        operation_description="댓글을 수정합니다.",
        request_body=CommentDetailRequestSerializer,
        responses={
            201: CommentSerializer,
            400: "Missing required fields",
            403: "password wrong",
            404: "author or post not found.",
        },
    )
    def put(self, request, comment_id):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "please signin"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2) 요청자(user)와 content 가져오기
        author = request.user
        content = request.data.get("content")

        try:
            comment = Comment.objects.get(id=comment_id)
        except:
            return Response(
                {"detail": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )
        author_info = request.data.get("author")
        content = request.data.get("content")

        # 필수 필드 체크
        if not (author_info and content is not None):
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        username = author_info.get("username")
        password = author_info.get("password")

        try:
            author = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)

        # 비밀번호 검증
        if not author.check_password(password):
            return Response({"detail": "Incorrect password."}, status=status.HTTP_403_FORBIDDEN)

        # 댓글 수정
        comment.content = content
        comment.save()
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_id="댓글 삭제",
        operation_description="댓글을 삭제합니다.",
        request_body=SignInRequestSerializer,
        responses={204: "No Content", 404: "Not Found", 400: "Bad Request"},
    )
    def delete(self, request, comment_id):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )
        author = request.user
        try:
            comment = Comment.objects.get(id=comment_id)
        except:
            return Response(
                {"detail": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )
        
        author_info = request.data

        # 필수 필드 체크
        if author_info is None:
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        username = author_info.get("username")
        password = author_info.get("password")

        try:
            author = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)

        # 비밀번호 검증
        if not author.check_password(password):
            return Response({"detail": "Incorrect password."}, status=status.HTTP_403_FORBIDDEN)
        # 본인이 쓴 댓글인지 검증
        if comment.author != author:
            return Response(
                    {"detail": "You are not the author of this comment."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)