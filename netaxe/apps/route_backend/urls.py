from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .authorization import FormulaTokenObtainPairView
from .views import MenuListByRoleId, CaptchaView, DashboardChart, WebSshView, DeviceCollectView, AutomationChart, \
    DispatchManageView

app_name = 'vue_backend'
urlpatterns = [

    path('login', FormulaTokenObtainPairView.as_view(), name='login'),
    path('getMenusByRoleId', MenuListByRoleId.as_view(), name='getMenusByRoleId'),
    path('captcha', CaptchaView.as_view(), name='captcha'),
    path('dashboardChart', DashboardChart.as_view(), name='dashboardChart'),
    path('deviceWebSsh', WebSshView.as_view(), name='deviceWebSsh'),
    path('deviceCollect', DeviceCollectView.as_view(), name='deviceCollect'),
    path('automationChart', AutomationChart.as_view(), name='automationChart'),
    path('dispatch_page/', csrf_exempt(DispatchManageView.as_view()), name='dispatch_page'),
]
