from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Allows access only to users with the 'admin' role.

    This permission class checks if the authenticated user has the 'admin' role.
    It can be used to restrict access to views or actions that should only be
    available to administrators.

    Usage Example:
        class SomeAdminView(APIView):
            permission_classes = [permissions.IsAuthenticated, IsAdmin]
            # View implementation...
    """

    def has_permission(self, request, view):
        return request.user and request.user.role == "admin"


class HasOwnerRole(permissions.BasePermission):
    """
    Allows access only to users with the 'owner' role.

    This permission class checks if the authenticated user has the 'owner' role.
    It is used to restrict access to views or actions that are intended for field
    owners, regardless of any specific object ownership.

    Note:
        - This permission does not check if the user owns a particular object.
          It only verifies the user's role.
        - For object-level ownership checks (e.g., ensuring the user owns a specific
          field or booking), use object-specific permissions like `IsOwnerOrReadOnly`
          or `IsObjectOwner`.

    Usage Example:
        class OwnerOnlyView(APIView):
            permission_classes = [permissions.IsAuthenticated, HasOwnerRole]
            # View implementation...
    """

    def has_permission(self, request, view):
        return request.user and request.user.role == "owner"


class IsOwnerRoleOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users with the 'owner' role to perform write operations.
    Read permissions are allowed to any request.
    """

    def has_permission(self, request, view):
        # Allow read-only methods for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write methods only if the user is authenticated and has the 'owner' role
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "owner"
        )
