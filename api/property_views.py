# property_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Trip, TripProperty, TripPropertyValue
from .serializers import TripPropertySerializer, TripPropertyValueSerializer


# -------------------------------------------------
# 1. عرض جميع الخصائص
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def list_properties_view(request):
    properties = TripProperty.objects.all()
    serializer = TripPropertySerializer(properties, many=True)
    return Response(serializer.data)


# -------------------------------------------------
# 2. إنشاء خاصية جديدة (مزود خدمة فقط)
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_property_view(request):
    if not request.user.is_provider:
        return Response({"error": "غير مسموح لك بإنشاء خصائص"}, status=403)

    serializer = TripPropertySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# -------------------------------------------------
# 3. تعديل خاصية
# -------------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_property_view(request, property_id):
    trip_property = get_object_or_404(TripProperty, id=property_id)

    if not request.user.is_provider:
        return Response({"error": "غير مسموح لك بتعديل الخصائص"}, status=403)

    serializer = TripPropertySerializer(trip_property, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


# -------------------------------------------------
# 4. حذف خاصية
# -------------------------------------------------
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_property_view(request, property_id):
    trip_property = get_object_or_404(TripProperty, id=property_id)

    if not request.user.is_provider:
        return Response({"error": "غير مسموح لك بحذف الخصائص"}, status=403)

    trip_property.delete()
    return Response({"message": "تم حذف الخاصية بنجاح"}, status=204)


# -------------------------------------------------
# 5. إضافة قيمة خاصية لرحلة
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_property_value_view(request, trip_id):
    if not request.user.is_provider:
        return Response({"error": "غير مسموح لك بإضافة قيم الخصائص"}, status=403)

    trip = get_object_or_404(Trip, id=trip_id)
    serializer = TripPropertyValueSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(trip=trip)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# -------------------------------------------------
# 6. تعديل قيمة خاصية
# -------------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_property_value_view(request, value_id):
    prop_value = get_object_or_404(TripPropertyValue, id=value_id)

    if not request.user.is_provider:
        return Response({"error": "غير مسموح لك بتعديل قيم الخصائص"}, status=403)

    serializer = TripPropertyValueSerializer(prop_value, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


# -------------------------------------------------
# 7. حذف قيمة خاصية
# -------------------------------------------------
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_property_value_view(request, value_id):
    prop_value = get_object_or_404(TripPropertyValue, id=value_id)

    if not request.user.is_provider:
        return Response({"error": "غير مسموح لك بحذف قيم الخصائص"}, status=403)

    prop_value.delete()
    return Response({"message": "تم حذف قيمة الخاصية بنجاح"}, status=204)
@api_view(['GET'])
@permission_classes([AllowAny])  # متاحة للجميع
def property_detail_view(request, property_id):
    """
    عرض تفاصيل خاصية رحلة محددة
    """
    trip_property = get_object_or_404(TripProperty, id=property_id)
    serializer = TripPropertySerializer(trip_property)
    return Response(serializer.data, status=status.HTTP_200_OK)