from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Announcement
from .serializers import AnnouncementSerializer
from .permissions import IsAdminAccount
# --------------------------------------------------
# 📢 عرض كل الإعلانات
# --------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])  # يمكن لأي شخص يشاهد الإعلانات
def list_announcements(request):
    announcements = Announcement.objects.all().order_by("-created_at")
    serializer = AnnouncementSerializer(announcements, many=True)
    return Response(serializer.data)


# --------------------------------------------------
# 📢 عرض إعلان محدد
# --------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def announcement_detail(request, announcement_id):
    try:
        announcement = Announcement.objects.get(id=announcement_id)
    except Announcement.DoesNotExist:
        return Response({"error": "الإعلان غير موجود"}, status=status.HTTP_404_NOT_FOUND)

    serializer = AnnouncementSerializer(announcement)
    return Response(serializer.data)


# --------------------------------------------------
# ➕ إنشاء إعلان
# --------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated,IsAdminAccount])  # فقط المستخدمين المسجلين
def create_announcement(request):
    serializer = AnnouncementSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------------------------------------
# ✏️ تعديل إعلان
# --------------------------------------------------
@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated,IsAdminAccount])
def update_announcement(request, announcement_id):
    try:
        announcement = Announcement.objects.get(id=announcement_id)
    except Announcement.DoesNotExist:
        return Response({"error": "الإعلان غير موجود"}, status=status.HTTP_404_NOT_FOUND)

    serializer = AnnouncementSerializer(announcement, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------------------------------------
# ❌ حذف إعلان
# --------------------------------------------------
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_announcement(request, announcement_id):
    try:
        announcement = Announcement.objects.get(id=announcement_id)
    except Announcement.DoesNotExist:
        return Response({"error": "الإعلان غير موجود"}, status=status.HTTP_404_NOT_FOUND)

    announcement.delete()
    return Response({"message": "تم حذف الإعلان بنجاح"}, status=status.HTTP_204_NO_CONTENT)
