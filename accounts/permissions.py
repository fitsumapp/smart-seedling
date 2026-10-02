"""Role-based permissions for views and API endpoints."""

from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class IsSuperAdminUser(BasePermission):
    """Allows access only to Super Admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_super_admin
        )


class IsNurseryAdminUser(BasePermission):
    """Allows access to Nursery Administrators and Super Admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_nursery_admin
        )


class IsOperatorUser(BasePermission):
    """Allows access to Operators, Nursery Admins, and Super Admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_operator
        )


class HasNurseryAccess(BasePermission):
    """Object-level permission checking if user has access to the nursery/zone/device."""
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_super_admin:
            return True
        
        # Check if obj itself is a Nursery
        from nursery.models import Nursery
        if isinstance(obj, Nursery):
            nursery = obj
        else:
            nursery = getattr(obj, 'nursery', None)
            if nursery is None and hasattr(obj, 'nursery_zone') and obj.nursery_zone:
                nursery = obj.nursery_zone.nursery
            elif nursery is None and hasattr(obj, 'device') and obj.device and obj.device.nursery_zone:
                nursery = obj.device.nursery_zone.nursery

        if nursery is not None:
            return request.user.can_manage_nursery(nursery)
            
        return False

