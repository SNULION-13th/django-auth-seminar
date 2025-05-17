from django.contrib import admin
from .models import UserProfile  # ✅ UserProfile 모델 불러오기

admin.site.register(UserProfile)  # ✅ UserProfile을 관리자 페이지에 등록!
