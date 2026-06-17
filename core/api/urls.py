from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    # path('', include('knox.urls')),
    path("login/", views.KnoxLogin.as_view(), name="login"),
    path(
        "accounts/password_change/",
        views.PasswordChange.as_view(),
        name="api_password_change",
    ),
    # path('login/', views.Login.as_view(), name='login'),
    path(
        "sync/pull/", views.PullRequestView.as_view({"get": "list"}), name="sync_pull"
    ),
    path(
        "sync/pull-deleted/",
        views.PullDeletedRequestView.as_view({"get": "list"}),
        name="sync_pull_deleted",
    ),
    path(
        "sync/push/",
        views.PushRequestView.as_view({"post": "upsert"}),
        name="sync_push",
    ),
    path(
        "sync/push-deleted/",
        views.PushDeletedRecordsView.as_view({"post": "soft_delete_records"}),
        name="sync_push_deleted",
    ),
    path(
        "sync/upload-images/",
        views.UploadImages.as_view({"post": "upload"}),
        name="sync_upload_images",
    ),
    path(
        "sync/pull-images-meta/",
        views.GetSyncImagesMetaView.as_view({"post": "list"}),
        name="sync_pull_images_meta",
    ),
    path(
        "sync/push-deleted-images/",
        views.PushDeletedImagesView.as_view({"post": "delete_images"}),
        name="sync_push_deleted_images",
    ),
    path(
        "sync/current_time_millis/",
        views.GetCurrentTimeMillis.as_view(),
        name="sync_current_time_millis",
    ),
]
