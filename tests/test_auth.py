"""Unit tests for authentication and role-based permissions."""

from django.test import TestCase, RequestFactory
from accounts.models import User, UserRole
from nursery.models import Nursery, NurseryZone
from accounts.permissions import (
    IsSuperAdminUser,
    IsNurseryAdminUser,
    IsOperatorUser,
    HasNurseryAccess
)


class AuthPermissionsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.nursery1 = Nursery.objects.create(name="Nursery One", code="NUR-1")
        self.nursery2 = Nursery.objects.create(name="Nursery Two", code="NUR-2")
        self.zone1 = NurseryZone.objects.create(nursery=self.nursery1, name="Zone 1", code="Z1")

        self.super_admin = User.objects.create_user(
            username="super", password="pwd", role=UserRole.SUPER_ADMIN, is_superuser=True
        )
        self.nursery_admin = User.objects.create_user(
            username="nursery_boss", password="pwd", role=UserRole.NURSERY_ADMIN, assigned_nursery=self.nursery1
        )
        self.operator = User.objects.create_user(
            username="op_user", password="pwd", role=UserRole.OPERATOR, assigned_nursery=self.nursery1
        )

    def test_permission_classes_view_level(self):
        request = self.factory.get('/')

        perm_super = IsSuperAdminUser()
        perm_nursery = IsNurseryAdminUser()
        perm_operator = IsOperatorUser()

        # Super Admin
        request.user = self.super_admin
        self.assertTrue(perm_super.has_permission(request, None))
        self.assertTrue(perm_nursery.has_permission(request, None))
        self.assertTrue(perm_operator.has_permission(request, None))

        # Nursery Admin
        request.user = self.nursery_admin
        self.assertFalse(perm_super.has_permission(request, None))
        self.assertTrue(perm_nursery.has_permission(request, None))
        self.assertTrue(perm_operator.has_permission(request, None))

        # Operator
        request.user = self.operator
        self.assertFalse(perm_super.has_permission(request, None))
        self.assertFalse(perm_nursery.has_permission(request, None))
        self.assertTrue(perm_operator.has_permission(request, None))

    def test_has_nursery_access_object_level(self):
        request = self.factory.get('/')
        perm = HasNurseryAccess()

        request.user = self.nursery_admin
        self.assertTrue(perm.has_object_permission(request, None, self.nursery1))
        self.assertTrue(perm.has_object_permission(request, None, self.zone1))
        self.assertFalse(perm.has_object_permission(request, None, self.nursery2))

        request.user = self.super_admin
        self.assertTrue(perm.has_object_permission(request, None, self.nursery2))
