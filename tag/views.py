from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tag
from .serializers import TagSerializer

from post.models import Post
from post.serializers import PostSerializer
from drf_yasg.utils import swagger_auto_schema

class TagListView(APIView):
  @swagger_auto_schema(
    operation_id='태그 목록 조회',
    operation_description='태그 목록을 조회합니다.',
    responses={200: TagSerializer(many=True)}
  )
  def get(self, request):
    tags = Tag.objects.all()
    serializer = TagSerializer(instance=tags, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

  @swagger_auto_schema(
    operation_id='태그 생성',
    operation_description='태그를 생성합니다.',
    request_body=TagSerializer,
    responses={201: TagSerializer}
  )
  def post(self, request):
    content = request.data.get('content')
    
    if not content:
      return Response({"detail": "missing fields ['content']"}, status=status.HTTP_400_BAD_REQUEST)

    if Tag.objects.filter(content=content).exists():
      return Response({"detail" : "Tag with same content already exists"}, status=status.HTTP_409_CONFLICT)

    tag = Tag.objects.create(content=content)
    serializer = TagSerializer(instance = tag)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
 
 
class TagDetailView(APIView):
  @swagger_auto_schema(
    operation_id='태그 내부 게시물 조회',
    operation_description='해당 태그가 달린 게시물을 조회합니다.',
    responses={200: PostSerializer(many=True), 204: 'No Content'}
  )
  def get(self, request, tag_id):
    try:
      Tag.objects.get(id=tag_id)
    except:
      return Response({"detail": "Provided tag does not exist."}, status=status.HTTP_204_NO_CONTENT)
    
    posts = Post.objects.filter(tags=tag_id)
    serializer = PostSerializer(instance=posts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
