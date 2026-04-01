# =====================================================
# IMPORTS
# =====================================================
import logging
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.views.generic import TemplateView

from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import (
    Customer, Category, Book, Download, Favorite,
    Announcement, CompanyInfo, LibraryInfo, Notification, AdminNotification,
    View, Reading, Rating
)
from .serializers import (
    CustomerSerializer, CategorySerializer, BookSerializer,
    FavoriteSerializer, AnnouncementSerializer,
    CompanyInfoSerializer, LibraryInfoSerializer
)
from .auth import CookieJWTAuthentication
from .permissions import IsAdminAccount

logger = logging.getLogger(__name__)


# =====================================================
# CATEGORIES
# =====================================================

from rest_framework.permissions import IsAuthenticated

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    authentication_classes = [CookieJWTAuthentication]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']

    def get_permissions(self):
        if self.request.method == "POST":
            # السماح لأي مستخدم مسجل
            return [IsAuthenticated()]
        return [AllowAny()]



class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [CookieJWTAuthentication]

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminAccount()]
        return [AllowAny()]


# =====================================================
# BOOKS
# =====================================================

class BookListView(generics.ListAPIView):
    queryset = Book.objects.all().order_by('-created_at')
    serializer_class = BookSerializer
    permission_classes = [AllowAny]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author']
    ordering_fields = ['created_at', 'download_count']

from rest_framework.permissions import IsAuthenticated

class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]  # السماح لأي مستخدم مسجل


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    authentication_classes = [CookieJWTAuthentication]

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]

# ==========================================
# تعديل / حذف كتاب واحد
# ==========================================
class BookRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    authentication_classes = [CookieJWTAuthentication]

    def get_permissions(self):
        # أي مستخدم يمكنه عرض تفاصيل الكتاب
        if self.request.method in ["GET"]:
            return [permissions.AllowAny()]

        # التعديل والحذف فقط لمنشئ الكتاب أو الأدمن
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        book = self.get_object()
        user = self.request.user

        if user != book.created_by and not user.is_staff:
            raise PermissionDenied("ليس لديك صلاحية تعديل هذا الكتاب")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user != instance.created_by and not user.is_staff:
            raise PermissionDenied("ليس لديك صلاحية حذف هذا الكتاب")

        instance.delete()

# =====================================================
# DOWNLOAD
# =====================================================

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def download_book_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    Download.objects.get_or_create(user=request.user, book=book)
    # عداد التحميل يتم تحديثه تلقائيًا عبر signals
    return Response({"message": "تم تحميل الكتاب"})


# =====================================================
# INTERACTIONS
# =====================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    View.objects.create(user=request.user, book=book)
    return Response({"message": "view added"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_reading(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    Reading.objects.create(user=request.user, book=book)
    return Response({"message": "reading added"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_book(request, book_id):
    value = int(request.data.get("value", 0))
    if value < 1 or value > 5:
        return Response({"error": "rating must be between 1 and 5"}, status=400)

    book = get_object_or_404(Book, id=book_id)
    Rating.objects.update_or_create(
        user=request.user,
        book=book,
        defaults={"value": value}
    )
    return Response({"message": "rating saved"})


# =====================================================
# FAVORITES
# =====================================================

from rest_framework.pagination import PageNumberPagination

class FavoritePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = FavoritePagination

    def get_queryset(self):
        user = self.request.user
        search = self.request.query_params.get('search', '')
        qs = Favorite.objects.filter(user=user).select_related('book')
        if search:
            qs = qs.filter(book__title__icontains=search)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}  # ✅ لتمكين build_absolute_uri


@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def toggle_favorite_view(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, book=book)

    if not created:
        favorite.delete()
        return Response({"message": "removed from favorites"})
    return Response({"message": "added to favorites"})


# =====================================================
# MY LIBRARY (كتب المستخدم نفسه)
# =====================================================

@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def my_library_view(request):
    books = Book.objects.filter(created_by=request.user).select_related('category')

    data = []
    for b in books:
        cover_url = request.build_absolute_uri(b.cover.url) if b.cover else None
        file_url = request.build_absolute_uri(b.file.url) if b.file else None

        data.append({
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "cover": cover_url,
            "file": file_url,
            "category": {"id": b.category.id, "name": b.category.name} if b.category else None,
            "created_at": b.created_at,
            "downloads": b.download_count,
            "favorites": b.favorites_count,
            "views": b.views_count,
            "average_rating": b.average_rating,
        })

    return Response({"status": "success", "results": data})


# =====================================================
# USER STATS (اعتمادًا على كتب المستخدم)
# =====================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_stats(request):
    user = request.user
    books = Book.objects.filter(created_by=user)

    total_views = books.aggregate(total=Count("views"))["total"] or 0
    total_readings = books.aggregate(total=Count("readings"))["total"] or 0
    total_downloads = books.aggregate(total=Count("downloads"))["total"] or 0
    total_favorites = books.aggregate(total=Count("favorites"))["total"] or 0
    total_ratings = Rating.objects.filter(book__created_by=user).count()

    return Response({
        "total_books": books.count(),
        "total_views": total_views,
        "total_readings": total_readings,
        "total_downloads": total_downloads,
        "total_favorites": total_favorites,
        "total_ratings": total_ratings,
    })


# =====================================================
# BOOK STATS
# =====================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def book_stats(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    distribution = (
        Rating.objects
        .filter(book=book)
        .values("value")
        .annotate(count=Count("id"))
    )

    return Response({
        "views": book.views_count,
        "readings": book.readings_count,
        "downloads": book.download_count,
        "favorites": book.favorites_count,
        "average_rating": book.average_rating,
        "ratings_distribution": distribution
    })


# =====================================================
# GLOBAL STATISTICS (ADMIN)
# =====================================================

class StatisticsView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "total_books": Book.objects.count(),
            "total_downloads": Download.objects.count(),
            "downloads_per_day": list(
                Download.objects
                .annotate(day=TruncDate('downloaded_at'))
                .values('day')
                .annotate(count=Count('id'))
                .order_by('-day')
            ),
            "top_books": list(
                Book.objects.order_by('-download_count')
                .values('title', 'download_count')[:5]
            )
        })


# =====================================================
# INFO
# =====================================================

class CompanyInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        info = CompanyInfo.objects.first()
        serializer = CompanyInfoSerializer(info)
        return Response({"status": "success", "data": serializer.data})


class LibraryInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        info = LibraryInfo.objects.first()
        serializer = LibraryInfoSerializer(info)
        return Response({"status": "success", "data": serializer.data})


# =====================================================
# ANNOUNCEMENTS
# =====================================================

class AnnouncementListView(generics.ListAPIView):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [AllowAny]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at']


@api_view(["GET"])
@permission_classes([AllowAny])
def top_books(request):
    books = (
        Book.objects
        .annotate(score=Count("favorites") + Count("downloads"))
        .order_by("-score")[:10]
    )

    data = [
        {
            "id": b.id,
            "title": b.title,
            "score": b.score,
            "rating": b.average_rating,
        }
        for b in books
    ]

    return Response(data)


# =====================================================
# FRONTEND
# =====================================================

class FrontendAppView(TemplateView):
    template_name = "index.html"



from django.db.models import Count, Q

@api_view(["GET"])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def my_books_stats(request):
    user = request.user

    books = (
        Book.objects
        .filter(created_by=user)
        .prefetch_related('ratings', 'printed_copies')
        .annotate(
            total_copies=Count('printed_copies', distinct=True),
            available_copies=Count(
                'printed_copies',
                filter=Q(printed_copies__status='available'),
                distinct=True
            ),
            borrowed_copies=Count(
                'printed_copies',
                filter=Q(printed_copies__status='borrowed'),
                distinct=True
            ),
            reserved_copies=Count(
                'printed_copies',
                filter=Q(printed_copies__status='reserved'),
                distinct=True
            ),
        )
    )

    data = []

    for b in books:
        ratings_distribution = (
            b.ratings.values('value')
            .annotate(count=Count('id'))
            .order_by('value')
        )

        data.append({
            "id": b.id,
            "title": b.title,

            # التفاعلات
            "views": b.views_count,
            "readings": b.readings_count,
            "downloads": b.download_count,
            "favorites": b.favorites_count,
            "average_rating": b.average_rating,
            "ratings_distribution": list(ratings_distribution),

            # النسخ المطبوعة
            "total_copies": b.total_copies,
            "available_copies": b.available_copies,
            "borrowed_copies": b.borrowed_copies,
            "reserved_copies": b.reserved_copies,
        })

    return Response({"results": data})

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import PrintedCopy
from .serializers import PrintedCopySerializer
from rest_framework.pagination import PageNumberPagination

# ==========================================
# Pagination
# ==========================================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# ==========================================
# List + Search + Pagination
# ==========================================

class PrintedCopyListCreateView(generics.ListCreateAPIView):
    queryset = PrintedCopy.objects.all().order_by('-added_at')
    serializer_class = PrintedCopySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['book__title', 'status', 'copy_number']

# ==========================================
# Retrieve, Update, Delete
# ==========================================

class PrintedCopyRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PrintedCopy.objects.all()
    serializer_class = PrintedCopySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
from rest_framework import generics, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .models import Announcement
from .serializers import AnnouncementSerializer
from rest_framework.pagination import PageNumberPagination
from .auth import CookieJWTAuthentication

# ==========================================
# Pagination
# ==========================================
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

# ==========================================
# List + Search + Pagination
# ==========================================
class AnnouncementListView(generics.ListAPIView):
    queryset = Announcement.objects.all().order_by("-created_at")
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]  # يمكن لأي مستخدم رؤية الإعلانات
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "title"]

# ==========================================
# Create
# ==========================================
class AnnouncementCreateView(generics.CreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]  # فقط المستخدمين المسجلين

# ==========================================
# Retrieve + Update + Delete
# ==========================================
class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    authentication_classes = [CookieJWTAuthentication]

    def get_permissions(self):
        # السماح فقط لمنشئ الإعلان أو الأدمن بالتعديل والحذف
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from .models import PrintedCopyRequest, PrintedCopy
from .serializers import PrintedCopyRequestSerializer


# =====================================================
# عرض جميع الطلبات
# =====================================================

class PrintedCopyRequestListView(generics.ListAPIView):
    serializer_class = PrintedCopyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # الأدمن يرى كل الطلبات
        if user.account_type == "admin":
            return PrintedCopyRequest.objects.all()

        # المستخدم يرى طلباته فقط
        return PrintedCopyRequest.objects.filter(user=user)


# =====================================================
# تقديم طلب جديد
# =====================================================

class PrintedCopyRequestCreateView(generics.CreateAPIView):
    serializer_class = PrintedCopyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# =====================================================
# تعديل الطلب (تغيير الحالة من قبل الأدمن)
# =====================================================

class PrintedCopyRequestUpdateView(generics.UpdateAPIView):
    serializer_class = PrintedCopyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PrintedCopyRequest.objects.all()

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        # فقط الأدمن يغير الحالة
        if user.account_type != "admin":
            raise PermissionDenied("ليس لديك صلاحية تعديل الطلب")

        new_status = self.request.data.get("status")

        if new_status == "approved":
            available_copy = PrintedCopy.objects.filter(
                book=instance.book,
                status="available"
            ).first()

            if available_copy:
                available_copy.status = "borrowed"
                available_copy.save()

                serializer.save(
                    status="approved",
                    printed_copy=available_copy,
                    approved_at=timezone.now()
                )
                return

        serializer.save()


# =====================================================
# حذف الطلب
# =====================================================

class PrintedCopyRequestDeleteView(generics.DestroyAPIView):
    serializer_class = PrintedCopyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PrintedCopyRequest.objects.all()

    def perform_destroy(self, instance):
        user = self.request.user

        # الأدمن يستطيع حذف أي طلب
        if user.account_type == "admin":
            instance.delete()
            return

        # المستخدم يستطيع حذف طلبه فقط إذا كان pending
        if instance.user == user and instance.status == "pending":
            instance.delete()
        else:
            raise PermissionDenied("لا يمكنك حذف هذا الطلب")
from rest_framework.permissions import IsAdminUser
class CompanyInfoUpdateView(generics.GenericAPIView):
    serializer_class = CompanyInfoSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        # جلب أول سجل موجود
        obj, created = CompanyInfo.objects.get_or_create(id=1)
        return obj

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
