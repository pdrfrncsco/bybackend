"""
Player privacy permission classes.

Each permission checks the Player.privacy_settings visibility level for the
corresponding domain (medical, contract, contact, documents, statistics)
and allows access only when the requesting user satisfies the visibility
constraint.

Visibility priorities (lowest -> highest restriction):
 - public: anyone
 - club: members of the player's current club's tenant (or staff)
 - organization: members of any tenant where the player has registrations (or staff)
 - agent: platform staff, the player's linked user, or users flagged as agents
 - private: only platform staff or the player themself

These classes are safe defaults for the migration window. They are defensive
(and tolerant of missing selectors/models in some test environments).
"""
from typing import Optional

from rest_framework.permissions import BasePermission


def _is_staff_or_self(request, player) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False):
        return True
    # If player has an associated User, allow them to view their own info
    try:
        if getattr(player, "user", None) and player.user_id == getattr(user, "id", None):
            return True
    except Exception:
        pass
    return False


def _user_belongs_to_tenant(user, tenant_id) -> bool:
    """Return True if user belongs to the given tenant_id.
    Uses TenantMembershipSelector.user_belongs_to_tenant when available; falls
    back to conservative False if unavailable.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    try:
        from accounts.selectors import TenantMembershipSelector

        return TenantMembershipSelector.user_belongs_to_tenant(user=user, tenant_id=tenant_id)
    except Exception:
        # Selector not available in this environment; conservatively deny
        return False


def _user_is_agent(user) -> bool:
    return bool(getattr(user, "is_agent", False))


def _player_current_registration_tenant(player) -> Optional[str]:
    try:
        # look for active registration (registered or loaned)
        reg = (
            player.registrations
            .filter(status__in=("registered", "loaned"))
            .select_related("club")
            .first()
        )
        if not reg:
            return None
        # clubs have tenant_id on the model in this codebase
        return getattr(reg.club, "tenant_id", None) or getattr(reg, "tenant_id", None)
    except Exception:
        return None


def _player_any_registration_tenants(player) -> list:
    try:
        return [getattr(r.club, "tenant_id", None) or getattr(r, "tenant_id", None) for r in player.registrations.all()]
    except Exception:
        return []


def _evaluate_visibility(request, player, visibility_level: str) -> bool:
    # Backwards compatibility: if privacy settings are not present for the player,
    # preserve previous permissive behavior and allow reads.
    try:
        if getattr(player, 'privacy_settings', None) is None:
            return True
    except Exception:
        # RelatedObjectDoesNotExist or other issues — allow to be permissive for migration window
        return True

    visibility_level = (visibility_level or "public").lower()

    if visibility_level == "public":
        return True

    # staff and self always allowed for non-public
    if _is_staff_or_self(request, player):
        return True

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if visibility_level == "private":
        return False

    if visibility_level == "agent":
        # allow agents (heuristic) and staff/self handled above
        return _user_is_agent(user)

    if visibility_level == "club":
        tenant_id = _player_current_registration_tenant(player)
        if tenant_id:
            return _user_belongs_to_tenant(user, tenant_id)
        return False

    if visibility_level == "organization":
        tenant_ids = _player_any_registration_tenants(player)
        for t in tenant_ids:
            if t and _user_belongs_to_tenant(user, t):
                return True
        return False

    # default conservative deny
    return False


class CanViewPlayerMedical(BasePermission):
    """Permission to view player medical info based on PlayerPrivacySettings.medical_visibility"""

    def has_object_permission(self, request, view, obj) -> bool:
        try:
            level = getattr(obj.privacy_settings, "medical_visibility", "private")
        except Exception:
            level = "private"
        return _evaluate_visibility(request, obj, level)


class CanViewPlayerContract(BasePermission):
    """Permission to view player contract info based on PlayerPrivacySettings.contract_visibility"""

    def has_object_permission(self, request, view, obj) -> bool:
        try:
            level = getattr(obj.privacy_settings, "contract_visibility", "club")
        except Exception:
            level = "club"
        return _evaluate_visibility(request, obj, level)


class CanViewPlayerContact(BasePermission):
    """Permission to view player contact info based on PlayerPrivacySettings.contact_visibility"""

    def has_object_permission(self, request, view, obj) -> bool:
        try:
            level = getattr(obj.privacy_settings, "contact_visibility", "club")
        except Exception:
            level = "club"
        return _evaluate_visibility(request, obj, level)


class CanViewPlayerDocuments(BasePermission):
    """Permission to view player documents based on PlayerPrivacySettings.documents_visibility"""

    def has_object_permission(self, request, view, obj) -> bool:
        try:
            level = getattr(obj.privacy_settings, "documents_visibility", "club")
        except Exception:
            level = "club"
        return _evaluate_visibility(request, obj, level)


class CanViewPlayerStatistics(BasePermission):
    """Permission to view player statistics based on PlayerPrivacySettings.statistics_visibility"""

    def has_object_permission(self, request, view, obj) -> bool:
        try:
            level = getattr(obj.privacy_settings, "statistics_visibility", "public")
        except Exception:
            level = "public"
        return _evaluate_visibility(request, obj, level)
