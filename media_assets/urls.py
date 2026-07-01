"""
BOLAYETU — Media Assets URL Configuration
"""

from django.urls import path

from media_assets.views import (
    MediaAssetDetailView,
    MediaAssetListView,
    MediaAssetSignedUrlView,
    MediaAssetUploadView,
)

app_name = "media_assets"

urlpatterns = [
    # Upload
    path("upload/", MediaAssetUploadView.as_view(), name="upload"),
    # List
    path("", MediaAssetListView.as_view(), name="list"),
    # Detail / Delete
    path("<uuid:asset_id>/", MediaAssetDetailView.as_view(), name="detail"),
    # Signed URL
    path("<uuid:asset_id>/signed-url/", MediaAssetSignedUrlView.as_view(), name="signed-url"),
]
