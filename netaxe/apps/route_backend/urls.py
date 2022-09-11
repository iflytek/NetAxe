from django.urls import path
from .authorization import FormulaTokenObtainPairView
from .views import MenuListByRoleId, CaptchaView, DashboardChart, WebSshView

app_name = 'vue_backend'
urlpatterns = [

    path('login', FormulaTokenObtainPairView.as_view(), name='login'),
    path('getMenusByRoleId', MenuListByRoleId.as_view(), name='getMenusByRoleId'),
    path('captcha', CaptchaView.as_view(), name='captcha'),
    path('dashboardChart', DashboardChart.as_view(), name='dashboardChart'),
    path('deviceWebSsh', WebSshView.as_view(), name='deviceWebSsh'),
]
