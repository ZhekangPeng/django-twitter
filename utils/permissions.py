from rest_framework.permissions import BasePermission

class IsObjectOwner(BasePermission):

    message = "You must be the owner of the object"

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
