from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    Read permissions are allowed to any request.
    """

    def has_permission(self, request, view):
        # Allow read-only methods for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to admins
        return request.user and request.user.is_staff
