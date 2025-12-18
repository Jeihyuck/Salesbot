from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    # path('kakao/view/', views.kakaoMessageView, name='kakaoMessageView'),
    path('channel/', views.channel.as_view()),
    path('util/', views.util.as_view()),
    path('menu/', views.menu.as_view()),
    path('table/', views.table.as_view()),
    path('api/', views.api.as_view()),
    path('code/', views.code.as_view()),
    path('file/get/<str:filename>/', views.getFile.as_view()),
    path('grpc/<str:gpu_server>/<str:function>/', views.grpc.as_view()),
]
