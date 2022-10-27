from django.urls import path, include
from rest_framework import routers

from apps.system.views.api_white_list import ApiWhiteListViewSet
from apps.system.views.area import AreaViewSet
from apps.system.views.dept import DeptViewSet
from apps.system.views.login_log import LoginLogViewSet
from apps.system.views.menu import MenuViewSet
from apps.system.views.menu_button import MenuButtonViewSet
from apps.system.views.operation_log import OperationLogViewSet
from apps.system.views.role import RoleViewSet


router = routers.SimpleRouter()
router.register(r'menu', MenuViewSet)
router.register(r'menu_button', MenuButtonViewSet)
router.register(r'role', RoleViewSet)
router.register(r'dept', DeptViewSet)
router.register(r'operation_log', OperationLogViewSet)
router.register(r'area', AreaViewSet)
router.register(r'api_white_list', ApiWhiteListViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
    path('login_log/', LoginLogViewSet.as_view({'get': 'list'})),
    path('login_log/<int:pk>/', LoginLogViewSet.as_view({'get': 'retrieve'})),
    path('dept_lazy_tree/', DeptViewSet.as_view({'get': 'dept_lazy_tree'})),
]