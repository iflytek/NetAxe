"""netboost URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from netboost import views
from drf_yasg import openapi
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from apps.system.views.login import (
    LoginView,
    LogoutView,
    LoginViewSet,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView
)


schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/login/', views.extend_admin_login),
    re_path(r'^captcha/', include('captcha.urls')),
    # path("swagger/",schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui",),
    re_path('^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # 登录
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/status/", LoginViewSet.as_view(), name="status"),
    path('api/token/', TokenObtainPairView.as_view(), name='get_jwt_token'),
    path("api/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # 自定义权限
    path("api/users/", include("apps.users.urls")),
    path("api/system/", include("apps.system.urls")),

    path(r'api/asset/', include('apps.asset.urls')),
    path(r'api/backend/', include('apps.route_backend.urls')),
    path(r'api/automation/', include('apps.automation.urls')),
    path(r'api/config_center/', include('apps.config_center.urls')),
    path(r'api/int_utilization/', include('apps.int_utilization.urls')),
]
