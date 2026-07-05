"""
BOLAYETU — Competition serializer helpers.

Shared presentation helpers for competitions and match center serializers.
"""


def get_club_logo_url(club) -> str:
    """
    Resolve the club logo through the DAM.

    Clubs no longer expose a legacy `logo` field directly, so competition
    serializers must fetch the URL from MediaAsset/MediaUsage.
    """

    if not club:
        return ""

    try:
        from media_assets.constants import AssetCategory, OwnerType
        from media_assets.services import MediaAssetService

        return (
            MediaAssetService.get_usage_url(
                owner_type=OwnerType.CLUB,
                owner_id=club.id,
                role=AssetCategory.LOGO,
            )
            or ""
        )
    except Exception:
        return ""
