from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin_user(user):
    return bool(user and getattr(user, 'is_authenticated', False) and (
        getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
    ))


class IsAdminUserCustom(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and getattr(request.user, 'is_authenticated', False))
        return is_admin_user(request.user)
