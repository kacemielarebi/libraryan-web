import os
import sys
from dotenv import load_dotenv

# 🟢 تحميل متغيرات البيئة من .env
load_dotenv()

# 🟢 إعداد بيئة Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

# 🔁 استيراد تطبيق Django الأساسي
from django.core.asgi import get_asgi_application

# 🔁 استيراد الميدلوير والموجهات
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api.middleware import TokenAuthMiddleware
from api.routing import websocket_urlpatterns

# 🟢 التطبيق الرئيسي
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(  # الميدلوير المخصص
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
