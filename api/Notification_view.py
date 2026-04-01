from rest_framework import generics
from django.db.models import Q
from .models import Notification, AdminNotification
from .serializers import NotificationSerializer, AdminNotificationSerializer
from .permissions import IsAdminAccount
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

# ✅ عرض إشعارات العميل
class CustomerNotificationsListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user  # بدل recipient
        ).order_by('-created_at')


# ✅ وضع الإشعار كمقروء (للعملاء)
class MarkCustomerNotificationReadView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)  # بدل recipient

    def perform_update(self, serializer):
        serializer.save(is_read=True)


# ✅ عرض إشعارات المشرف (الخاصة والعامة)
class AdminNotificationsListView(generics.ListAPIView):
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.account_type != 'admin':
            return AdminNotification.objects.none()
        return AdminNotification.objects.filter(
            Q(recipient=user) | Q(recipient__isnull=True)
        ).order_by('-created_at')


# ✅ وضع الإشعار كمقروء (للمشرفين)
class MarkAdminNotificationReadView(generics.UpdateAPIView):
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AdminNotification.objects.filter(recipient=user)

    def perform_update(self, serializer):
        serializer.save(is_read=True)


# ✅ عرض عدد الإشعارات غير المقروءة (للعميل والمشرف)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_notifications_count(request):
    if request.user.account_type == 'admin':
        count = AdminNotification.objects.filter(recipient=request.user, is_read=False).count()
    else:
        count = Notification.objects.filter(user=request.user, is_read=False).count()  # بدل recipient
    return Response({"unread_count": count})