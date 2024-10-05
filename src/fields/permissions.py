from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to anyone,
        # write permissions are only allowed to the owner.
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners or related users to access the object.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == 'user':
            return obj.user == user
        elif user.role == 'owner':
            return obj.field.owner == user
        elif user.role == 'admin':
            return True
        return False
