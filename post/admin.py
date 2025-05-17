from django.contrib import admin
from .models import Post  # ✅ Post 모델 가져오기

admin.site.register(Post)  # ✅ Post 모델을 관리자 페이지에 등록!
