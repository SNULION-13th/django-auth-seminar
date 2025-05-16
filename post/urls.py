from django.urls import path
### 추가
from .views import PostListView, PostDetailView, LikeView
###

app_name = 'post'
urlpatterns = [
    # CBV url path
    path("", PostListView.as_view()), ### 추가
    path("<int:post_id>/", PostDetailView.as_view()), ### 추가
    path("<int:post_id>/like/", LikeView.as_view()), ### 추가
]