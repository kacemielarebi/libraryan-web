# auth/auth.py
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(JWTAuthentication):
    """
    مصادقة JWT من الكوكيز مع دعم التجديد التلقائي إذا انتهى الـ access_token.
    """

    def enforce_csrf(self, request):
        # تعطيل فحص CSRF (اختياري)
        return

    def authenticate(self, request):
        access_token_str = request.COOKIES.get("access_token")
        refresh_token_str = request.COOKIES.get("refresh_token")

        if not access_token_str:
            logger.debug("لا يوجد access_token في الكوكيز")
            return None

        try:
            # محاولة التحقق من الـ access_token
            validated_token = self.get_validated_token(access_token_str)
            user = self.get_user(validated_token)
            return user, validated_token

        except TokenError as e:
            logger.info(f"Access token انتهى أو خطأ: {e}")

            if not refresh_token_str:
                logger.warning("لا يوجد refresh_token لتجديد access_token")
                return None

            try:
                refresh = RefreshToken(refresh_token_str)
                user = self.get_user(refresh)

                # إنشاء access_token جديد
                new_access = refresh.access_token
                new_access["account_type"] = getattr(user, "account_type", "customer")
                new_access["email"] = user.email

                # حفظ التوكن الجديد في request لتحديث الكوكيز
                request.new_access_token = str(new_access)

                logger.info("تم تجديد access_token بنجاح")
                return user, new_access

            except TokenError as e:
                logger.error(f"Refresh token انتهى أو خطأ: {e}")
                return None
