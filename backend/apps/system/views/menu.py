from rest_framework import serializers
from rest_framework.decorators import action

from apps.system.models import Menu
from utils.custom.json_response import SuccessResponse
from utils.custom.serializers import CustomModelSerializer
from utils.custom.viewset import CustomModelViewSet


class MenuSerializer(CustomModelSerializer):
    """
    菜单表的简单序列化器
    """
    children = serializers.SerializerMethodField()
    parentPath = serializers.SerializerMethodField()
    iconPrefix = serializers.SerializerMethodField()
    menuPermission = serializers.SerializerMethodField(read_only=True)

    def get_children(self, data):
        queryset = Menu.objects.filter(parent_id=data.id).all()
        children = MenuSerializer(queryset, many=True).data
        if children:
            return children
        else:
            return None

    def get_parentPath(self, instance):
        if instance.parent:
            return instance.parent.web_path
        else:
            return ""

    def get_iconPrefix(self, instance):
        return "iconfont"

    def get_menuPermission(self, instance):
        queryset = instance.menuPermission.order_by('-name').values_list('name', flat=True)
        if queryset:
            return queryset
        else:
            return None

    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class MenuCreateSerializer(CustomModelSerializer):
    """
    菜单表的创建序列化器
    """
    name = serializers.CharField(required=False)

    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class WebRouterSerializer(CustomModelSerializer):
    """
    前端菜单路由的简单序列化器
    """
    children = serializers.SerializerMethodField()
    menuPermission = serializers.SerializerMethodField(read_only=True)

    def get_children(self, data):
        queryset = Menu.objects.filter(parent_id=data.id, status=1).all()
        if not self.request.user.is_superuser:
            menuIds = self.request.user.role.values_list('menu__id', flat=True)
            queryset = Menu.objects.filter(id__in=menuIds, status=1, parent_id=data.id).all()
        children = WebRouterSerializer(queryset, many=True, request=self.request).data
        if children:
            return children
        else:
            return None

    def get_menuPermission(self, instance):
        # 判断是否是超级管理员
        if self.request.user.is_superuser:
            return instance.menuPermission.values_list('value', flat=True)
        else:
            # 根据当前角色获取权限按钮id集合
            permissionIds = self.request.user.role.values_list('permission', flat=True)
            queryset = instance.menuPermission.filter(id__in=permissionIds, menu=instance.id).values_list('value', flat=True)
            if queryset:
                return queryset
            else:
                return None

    class Meta:
        model = Menu
        fields = ('id', 'parent', 'icon', 'sort', 'name', 'is_link', 'is_catalog', 'web_path', 'component',
        'component_name', 'cache', 'visible', 'menuPermission', 'children')
        read_only_fields = ["id"]


class MenuViewSet(CustomModelViewSet):
    """
    菜单管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    create_serializer_class = MenuCreateSerializer
    update_serializer_class = MenuCreateSerializer
    search_fields = ['name', 'status']
    filterset_fields = {
        "parent": ["isnull"],
        "name": ["icontains"],
    }

    @action(methods=['GET'], detail=False, permission_classes=[])
    def web_router(self, request):
        """用于前端获取当前角色的路由"""
        queryset = self.queryset.filter(status=1, parent__isnull=True)
        if not self.request.user.is_superuser:
            menuIds = self.request.user.role.values_list('menu__id', flat=True)
            parentMenuIds = list(set(Menu.objects.filter(id__in=menuIds, status=1).values_list('parent_id', flat=True)))
            queryset = self.queryset.filter(status=1, id__in=parentMenuIds)
        serializer = WebRouterSerializer(queryset, many=True, request=request)
        data = serializer.data
        return SuccessResponse(data=data, total=len(data), msg="获取成功")
