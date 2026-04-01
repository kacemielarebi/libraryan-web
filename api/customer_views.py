from django.shortcuts import get_object_or_404
from django.db import models
from django.contrib.auth.hashers import check_password

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from .models import Customer
from .serializers import CustomerSerializer
from .auth import CookieJWTAuthentication  # ✅ إضافة المصادقة عبر الكوكي

# =====================================================
# Pagination
# =====================================================

class CustomerPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


# =====================================================
# 1️⃣ إنشاء حساب
# =====================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def create_customer_view(request):
    data = request.data
    required_fields = ['username', 'email', 'password']

    for field in required_fields:
        if not data.get(field):
            return Response({"error": f"حقل {field} مطلوب"}, status=400)

    email = data['email'].lower()
    if Customer.objects.filter(email=email).exists():
        return Response({"error": "البريد الإلكتروني مستخدم بالفعل"}, status=400)
    if Customer.objects.filter(username=data['username']).exists():
        return Response({"error": "اسم المستخدم مستخدم بالفعل"}, status=400)

    try:
        customer = Customer.objects.create_user(
            username=data['username'],
            email=email,
            password=data['password'],
            phone=data.get('phone', ''),
            address=data.get('address', '')
        )
        serializer = CustomerSerializer(customer)
        return Response({"message": "تم إنشاء الحساب بنجاح", "customer": serializer.data}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


# =====================================================
# 2️⃣ تعديل الحساب (باستخدام الكوكي لتحديد المستخدم)
# =====================================================

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_customer_view(request):
    customer = request.user
    data = request.data.copy()

    password = data.pop("password", None)
    if not password:
        return Response({"error": "الرجاء إدخال كلمة المرور لتأكيد التعديل"}, status=400)

    if not check_password(password, customer.password):
        return Response({"error": "كلمة المرور غير صحيحة"}, status=403)

    # منع تعديل الحقول الحساسة
    restricted_fields = ['account_type', 'is_staff', 'is_superuser', 'date_joined']
    for field in restricted_fields:
        if field in data:
            return Response({"error": f"لا يمكن تعديل حقل {field}"}, status=400)

    # التحقق من تكرار البريد واسم المستخدم
    if 'email' in data:
        new_email = data['email'].lower()
        if Customer.objects.filter(email=new_email).exclude(id=customer.id).exists():
            return Response({"error": "البريد الإلكتروني مستخدم بالفعل"}, status=400)
        customer.email = new_email

    if 'username' in data:
        if Customer.objects.filter(username=data['username']).exclude(id=customer.id).exists():
            return Response({"error": "اسم المستخدم مستخدم بالفعل"}, status=400)
        customer.username = data['username']

    allowed_fields = ['first_name', 'last_name', 'phone', 'address']
    for field in allowed_fields:
        if field in data:
            setattr(customer, field, data[field])

    customer.save()
    serializer = CustomerSerializer(customer)
    return Response({"message": "تم تحديث البيانات بنجاح", "customer": serializer.data})


# =====================================================
# 3️⃣ قائمة العملاء (للمشرف فقط مع البحث والترتيب)
# =====================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_customers_view(request):
    if not request.user.is_staff:
        return Response({"error": "غير مصرح لك بالوصول"}, status=403)

    customers = Customer.objects.all()

    # ===== البحث =====
    search = request.GET.get('search', '').strip()
    if search:
        customers = customers.filter(
            models.Q(username__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(phone__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search)
        )

    # ===== الترتيب =====
    ordering = request.GET.get('ordering', '-date_joined')
    allowed_ordering = ['username', 'email', 'date_joined',
                        '-username', '-email', '-date_joined']
    if ordering in allowed_ordering:
        customers = customers.order_by(ordering)

    # ===== الترقيم =====
    paginator = CustomerPagination()
    result_page = paginator.paginate_queryset(customers, request)
    serializer = CustomerSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)


# =====================================================
# 4️⃣ تفاصيل عميل
# =====================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_detail_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.user.id != customer.id and not request.user.is_staff:
        return Response({"error": "غير مصرح لك بعرض هذه البيانات"}, status=403)

    serializer = CustomerSerializer(customer)
    data = serializer.data

    if request.user.is_staff:
        data.update({
            "is_active": customer.is_active,
            "is_staff": customer.is_staff,
            "is_superuser": customer.is_superuser,
            "last_login": customer.last_login,
        })

    return Response(data)


# =====================================================
# 5️⃣ حذف عميل (للمشرف فقط)
# =====================================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_customer_view(request, customer_id):
    if not request.user.is_staff:
        return Response({"error": "غير مصرح لك بهذا الإجراء"}, status=403)

    customer = get_object_or_404(Customer, id=customer_id)

    if customer.id == request.user.id:
        return Response({"error": "لا يمكنك حذف حسابك الخاص"}, status=400)

    if customer.is_superuser:
        return Response({"error": "لا يمكن حذف المشرف الرئيسي"}, status=403)

    deleted_data = {
        "id": customer.id,
        "username": customer.username,
        "email": customer.email
    }

    customer.delete()
    return Response({"message": "تم حذف العميل بنجاح", "deleted_customer": deleted_data})
