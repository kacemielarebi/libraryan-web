from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
import json

from .models import Registration, Trip, RegistrationPerson, RegistrationDocument,RequiredDocument
from .serializers import RegistrationSerializer,RequiredDocumentSerializer,RegistrationPersonSerializer,RegistrationDocumentSerializer
from .permissions import IsAdminAccount


# ============================================================
# 📌 عرض التسجيلات بصلاحيات موحدة (مدمج)
# ============================================================
class BaseRegistrationListView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if IsAdminAccount().has_permission(self.request, self):
            return self.filter_queryset_all()
        return self.filter_queryset_customer(user)

    def filter_queryset_all(self):
        return Registration.objects.all()

    def filter_queryset_customer(self, customer):
        return Registration.objects.filter(customer=customer)

from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination


# 📌 تقسيم الصفحات: 50 عنصر في كل صفحة
class RegistrationPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ============================================================
# 🔄 دالة مشتركة للفلترة
# ============================================================
from django.db.models import Q

def filter_registrations(qs, params):
    if customer_name := params.get("customer_name"):
        qs = qs.filter(customer__username__icontains=customer_name)
    if customer_email := params.get("customer_email"):
        qs = qs.filter(customer__email__icontains=customer_email)
    if customer_phone := params.get("customer_phone"):
        qs = qs.filter(customer__phone__icontains=customer_phone)
    if customer_address := params.get("customer_address"):
        qs = qs.filter(customer__address__icontains=customer_address)

    if trip_name := params.get("trip_name"):
        qs = qs.filter(trip__name__icontains=trip_name)
    if trip_destination := params.get("trip_destination"):
        qs = qs.filter(trip__destination__icontains=trip_destination)
    if trip_type := params.get("trip_type"):
        qs = qs.filter(trip__type__icontains=trip_type)
    if trip_status := params.get("trip_status"):
        qs = qs.filter(trip__status__icontains=trip_status)

    if payment_status := params.get("payment_status"):
        qs = qs.filter(payment_status=payment_status)
    if registration_date := params.get("registration_date"):
        qs = qs.filter(registration_date=registration_date)

    return qs








# ============================================================
# 1️⃣ جميع التسجيلات
# ============================================================
class AllRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    pagination_class = RegistrationPagination
    permission_classes = [IsAuthenticated, IsAdminAccount]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["customer__username", "trip__name"]  # 🔍 البحث
    ordering_fields = ["registration_date", "payment_status"]  # 📌 الترتيب

    def get_queryset(self):
        qs = Registration.objects.all()
        return filter_registrations(qs, self.request.query_params)


# ============================================================
# 2️⃣ تسجيلات عميل
# ============================================================
class CustomerRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    pagination_class = RegistrationPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["trip__name"]
    ordering_fields = ["registration_date", "payment_status"]

    def get_queryset(self):
        customer_id = self.kwargs['customer_id']
        qs = Registration.objects.filter(customer_id=customer_id)
        return filter_registrations(qs, self.request.query_params)


# ============================================================
# 3️⃣ تسجيلات رحلة
# ============================================================
class TripRegistrationsView(generics.ListAPIView):
    serializer_class = RegistrationSerializer
    pagination_class = RegistrationPagination
    permission_classes = [IsAuthenticated, IsAdminAccount]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["customer__username"]
    ordering_fields = ["registration_date", "payment_status"]

    def get_queryset(self):
        trip_id = self.kwargs['trip_id']
        qs = Registration.objects.filter(trip_id=trip_id)
        return filter_registrations(qs, self.request.query_params)


# ============================================================
# 4️⃣ تفاصيل تسجيل
# ============================================================
class RegistrationDetailView(generics.RetrieveAPIView):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if IsAdminAccount().has_permission(self.request, self):
            return Registration.objects.all()
        return Registration.objects.filter(customer=user)


# ============================================================
# 5️⃣ تسجيل في رحلة (إنشاء تسجيل + أشخاص + وثائق)
# ============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def register_for_trip_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)

    # ⛔ التحقق من حالة الرحلة
    if trip.start_date > timezone.now().date() or trip.status in ['closed', 'cancelled']:
        return Response({"error": "لا يمكن التسجيل في هذه الرحلة"}, status=400)

    if trip.end_date< timezone.now().date():
        return Response({"error": "انتهى التسجيل لهذه الرحلة"}, status=400)

    if Registration.objects.filter(customer=request.user, trip=trip).exists():
        return Response({"error": "أنت مسجل بالفعل في هذه الرحلة"}, status=409)
    # ✅ حساب المقاعد المتبقية
    current_count = RegistrationPerson.objects.filter(registration__trip=trip).count()
    seats_left = trip.max_participants - current_count

    if seats_left <= 0:
        trip.status = 'full'
        trip.save(update_fields=['status'])
        return Response({"error": "اكتملت المقاعد في هذه الرحلة"}, status=400)

    # ✅ الأشخاص المسجلين
    persons_data = request.data.getlist('persons', [])
    if not persons_data:
        return Response({"error": "يجب إدخال بيانات الأشخاص المسجلين"}, status=400)

    if len(persons_data) > seats_left:
        return Response({
            "error": f"عدد المقاعد المتبقية ({seats_left}) لا يكفي لهذا العدد من الأشخاص"
        }, status=400)
    # ✅ إنشاء التسجيل
    registration = Registration.objects.create(
        customer=request.user,
        trip=trip,
        payment_status=request.data.get("payment_status", "unpaid"),
        documents_submitted=False
    )

    # ✅ الأشخاص المرتبطين بهذا التسجيل
    persons_data = request.data.getlist('persons', [])
    for idx, person_json in enumerate(persons_data):
        p_data = json.loads(person_json)
        person = RegistrationPerson.objects.create(
            registration=registration,
            full_name=p_data['full_name'],
            age_group=p_data['age_group'],
            age=p_data['age'],
        )

        # ✅ رفع الوثائق الخاصة بالشخص
        file_key = f"documents_{idx}"
        for file in request.FILES.getlist(file_key):
            RegistrationDocument.objects.create(person=person, file=file)

    serializer = RegistrationSerializer(registration)
    return Response(serializer.data, status=201)


# ============================================================
# 6️⃣ تعديل تسجيل
# ============================================================
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_registration_view(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)

    serializer = RegistrationSerializer(registration, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


# ============================================================
# 7️⃣ إلغاء تسجيل
# ============================================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_registration_view(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)

    # السماح فقط للعميل نفسه أو للمشرف
    if request.user != registration.customer and not IsAdminAccount().has_permission(request, view=None):
        return Response({"error": "غير مسموح لك بإلغاء هذا التسجيل"}, status=403)

    registration.delete()
    return Response({"message": "تم إلغاء التسجيل بنجاح"}, status=204)
# ============================================================
# 👤 جلب الأشخاص المرتبطين بتسجيل
# ============================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def registration_persons_view(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    persons = registration.persons.all()
    serializer = RegistrationPersonSerializer(persons, many=True)
    return Response(serializer.data)


# ============================================================
# 👤 إضافة شخص جديد لتسجيل
# ============================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_registration_person_view(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    data = request.data.copy()
    data['registration'] = registration.id
    serializer = RegistrationPersonSerializer(data=data)
    if serializer.is_valid():
        serializer.save(registration=registration)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# ============================================================
# 👤 تعديل/حذف شخص
# ============================================================
@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_delete_person_view(request, person_id):
    person = get_object_or_404(RegistrationPerson, id=person_id)

    if request.method == 'PUT':
        serializer = RegistrationPersonSerializer(person, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        person.delete()
        return Response({"detail": "تم الحذف بنجاح"}, status=204)
# ============================================================
# 📄 رفع/عرض وثائق لشخص
# ============================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def person_documents_view(request, person_id):
    person = get_object_or_404(RegistrationPerson, id=person_id)

    if request.method == 'GET':
        serializer = RegistrationDocumentSerializer(person.documents.all(), many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = RegistrationDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(person=person)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
# عرض القائمة + إنشاء جديد
class RequiredDocumentListCreateView(generics.ListCreateAPIView):
    queryset = RequiredDocument.objects.all()
    serializer_class = RequiredDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminAccount]


# عرض/تعديل/حذف عنصر واحد
class RequiredDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RequiredDocument.objects.all()
    serializer_class = RequiredDocumentSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated, IsAdminAccount]


# عرض حسب نوع الرحلة
class RequiredDocumentByTripTypeView(generics.ListAPIView):
    serializer_class = RequiredDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        trip_type = self.kwargs.get("trip_type")
        return RequiredDocument.objects.filter(trip_type=trip_type)