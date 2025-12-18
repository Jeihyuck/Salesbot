from django.urls import path, include
from . import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    # path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    # path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    # path('token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
    # path('kakao_callback/', views.kakaoCallback.as_view()),
    # path('kakao_login/', views.kakaoLogin.as_view()),
    # path('kakao/', views.kakao.as_view()),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),  
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
    # path('accounts/', include('django.contrib.auth.urls')),
    # path('changepassword/', views.ChangePassword.as_view()),
    # path('resetpassword/', views.ResetPassword.as_view()),
    # path('resetpasswordbyadmin/', views.ResetPasswordByAdmin.as_view()),
    # path('account/', views.Account.as_view()),
    path('misc/', views.misc.as_view()),
    path('login/', views.login.as_view()),
    path('account/', views.account.as_view()),
    path('permission/', views.permission.as_view()),
    path('meta/', views.meta.as_view()),
]
