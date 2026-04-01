from rest_framework.permissions import BasePermission

class IsAdminAccount(BasePermission):
    """
    يسمح فقط للمستخدمين الذين لديهم is_staff=True.
    """
    message = "ليس لديك صلاحية لتنفيذ هذا الإجراء. يجب أن تكون مشرفاً."
    def has_permission(self, request, view):
       
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff and
            getattr(request.user, "account_type", None) == "admin"
        )