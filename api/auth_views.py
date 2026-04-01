# views/auth_views.py
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer
from .serializers import CustomerSerializer, ChangePasswordSerializer
from .auth import CookieJWTAuthentication


# =====================================================
# HELPERS
# =====================================================

def set_auth_cookies(response, access_token=None, refresh_token=None):
    """
    حفظ access و refresh token في الكوكيز
    """
    cookie_params = {
        "httponly": True,
        "path": "/",
        "secure": not settings.DEBUG,
        "samesite": "None" if not settings.DEBUG else "Lax",
    }

    if access_token:
        response.set_cookie(
            "access_token",
            access_token,
            max_age=60 * 15,  # 15 دقيقة
            **cookie_params
        )

    if refresh_token:
        response.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=60 * 60 * 24 * 7,  # 7 أيام
            **cookie_params
        )

    return response


# =====================================================
# 1. CSRF TOKEN
# =====================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token_view(request):
    csrf_token = get_token(request)

    response = Response({
        "status": "success",
        "csrf_token": csrf_token
    })

    response.set_cookie(
        "csrftoken",
        csrf_token,
        httponly=False,
        secure=not settings.DEBUG,
        samesite="None" if not settings.DEBUG else "Lax",
        path="/"
    )
    return response


# =====================================================
# 2. ME
# =====================================================

@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = CustomerSerializer(request.user)

    response = Response({
        "status": "success",
        "data": serializer.data
    })

    # ✅ مهم: تحديث access_token إذا تم تجديده
    if hasattr(request, "new_access_token"):
        set_auth_cookies(response, access_token=request.new_access_token)

    return response


# =====================================================
# 3. LOGIN
# =====================================================

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    print("Received login request with data:", request.data)  # Debugging line
    email = request.data.get("email", "").strip()
    password = request.data.get("password", "")

    if not email or not password:
        return Response(
            {"message": "البريد وكلمة المرور مطلوبان"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = Customer.objects.get(email=email)

        if not user.check_password(password):
            raise Customer.DoesNotExist

        if not user.is_active:
            return Response(
                {"message": "الحساب غير مفعل"},
                status=status.HTTP_403_FORBIDDEN
            )

    except Customer.DoesNotExist:
        return Response(
            {"message": "بيانات الدخول غير صحيحة"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    refresh = RefreshToken.for_user(user)

    response = Response({
        "status": "success",
        "message": "تم تسجيل الدخول بنجاح",
        "data": {
            "user": CustomerSerializer(user).data
        }
    })

    # JWT cookies
    set_auth_cookies(
        response,
        access_token=str(refresh.access_token),
        refresh_token=str(refresh)
    )

    # CSRF cookie
    response.set_cookie(
        "csrftoken",
        get_token(request),
        httponly=False,
        secure=not settings.DEBUG,
        samesite="None" if not settings.DEBUG else "Lax",
        path="/"
    )

    return response


# =====================================================
# 4. LOGOUT
# =====================================================

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def logout_view(request):
    response = Response({
        "status": "success",
        "message": "تم تسجيل الخروج بنجاح"
    })

    for cookie in ["access_token", "refresh_token", "csrftoken"]:
        response.delete_cookie(cookie, path="/")

    return response


# =====================================================
# 5. CHANGE PASSWORD (للمستخدم المسجل)
# =====================================================

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={"request": request}
    )

    if serializer.is_valid():
        request.user.set_password(
            serializer.validated_data["new_password"]
        )
        request.user.save()
        return Response({
            "message": "تم تغيير كلمة المرور بنجاح"
        })

    return Response(serializer.errors, status=400)


# =====================================================
# 6. PASSWORD RESET (طلب رمز)
# =====================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    email = request.data.get("email")

    try:
        user = Customer.objects.get(email=email)
    except Customer.DoesNotExist:
        return Response({"message": "البريد غير موجود"}, status=404)

    reset_code = get_random_string(length=6, allowed_chars="0123456789")
    user.reset_code = reset_code
    user.save(update_fields=["reset_code"])

    send_mail(
        "استعادة كلمة المرور",
        f"رمز الاستعادة: {reset_code}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )

    return Response({"message": "تم إرسال رمز الاستعادة"})


# =====================================================
# 7. PASSWORD RESET CONFIRM
# =====================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    email = request.data.get("email")
    code = request.data.get("code")
    new_password = request.data.get("new_password")

    try:
        user = Customer.objects.get(email=email, reset_code=code)
    except Customer.DoesNotExist:
        return Response({"message": "رمز غير صالح"}, status=400)

    user.set_password(new_password)
    user.reset_code = None
    user.save()

    return Response({"message": "تم تغيير كلمة المرور بنجاح"})
