from django.utils.deprecation import MiddlewareMixin

class RefreshTokenMiddleware(MiddlewareMixin):
    """
    ميدل وير لتحديث access_token في الكوكي إذا تم تجديده.
    """

    def process_response(self, request, response):
        new_access = getattr(request, "new_access_token", None)
        if new_access:
            response.set_cookie(
                "access_token",
                new_access,
                httponly=True,
                secure=False,  # حط True في الإنتاج مع HTTPS
                samesite="Lax",  # أو "None" مع https
            )
        return response
