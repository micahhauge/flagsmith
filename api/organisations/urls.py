from app_analytics.views import (
    get_usage_data_total_count_view,
    get_usage_data_view,
)
from django.conf.urls import include, url
from django.urls import path
from rest_framework_nested import routers

from api_keys.views import MasterAPIKeyViewSet
from organisations.views import OrganisationWebhookViewSet
from users.views import FFAdminUserViewSet, UserPermissionGroupViewSet

from . import views
from .invites.views import InviteLinkViewSet, InviteViewSet
from .permissions.views import (
    UserOrganisationPermissionViewSet,
    UserPermissionGroupOrganisationPermissionViewSet,
)

router = routers.DefaultRouter()
router.register(r"", views.OrganisationViewSet, basename="organisation")

organisations_router = routers.NestedSimpleRouter(router, r"", lookup="organisation")
organisations_router.register(
    r"invites", InviteViewSet, basename="organisation-invites"
)
organisations_router.register(
    r"invite-links", InviteLinkViewSet, basename="organisation-invite-links"
)
organisations_router.register(
    r"users", FFAdminUserViewSet, basename="organisation-users"
)
organisations_router.register(
    r"groups", UserPermissionGroupViewSet, basename="organisation-groups"
)
organisations_router.register(
    r"webhooks", OrganisationWebhookViewSet, basename="organisation-webhooks"
)
organisations_router.register(
    r"master-api-keys", MasterAPIKeyViewSet, basename="organisation-master-api-keys"
)
organisations_router.register(
    "user-permissions",
    UserOrganisationPermissionViewSet,
    basename="organisation-user-permission",
)
organisations_router.register(
    "user-group-permissions",
    UserPermissionGroupOrganisationPermissionViewSet,
    basename="organisation-user-group-permission",
)
app_name = "organisations"

urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^", include(organisations_router.urls)),
    path(
        "org/<int:organisation_pk>/usage-data/",
        get_usage_data_view,
        name="usage-data",
    ),
    path(
        "org/<int:organisation_pk>/usage-data/total-count",
        get_usage_data_total_count_view,
        name="usage-data-total-count",
    ),
]
