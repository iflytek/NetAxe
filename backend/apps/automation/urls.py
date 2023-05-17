from django.urls import path, include
from rest_framework_extensions.routers import (
    ExtendedDefaultRouter as DefaultRouter
)

from .views import CollectionPlanViewSet


router = DefaultRouter()
router.register(r'collection_plan', CollectionPlanViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
]
