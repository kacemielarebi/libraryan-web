# auth/middleware.py

class RefreshAccessTokenMiddleware:
    """
    يقوم بوضع access_token الجديد في الكوكيز تلقائيًا إذا تم تجديده.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if hasattr(request, "new_access_token"):
            response.set_cookie(
                "access_token",
                request.new_access_token,
                httponly=True,
                secure=False,   # False للتطوير المحلي
                samesite="Lax",
                path="/"
            )

        return response
