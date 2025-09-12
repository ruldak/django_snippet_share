from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission untuk hanya mengizinkan pemilik suatu object untuk mengeditnya.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions diizinkan untuk request apapun
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions hanya diizinkan untuk pemilik snippet
        return obj.user == request.user