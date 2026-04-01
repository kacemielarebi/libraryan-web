from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    Customer, Category, Book, Download, Favorite,
    Announcement, CompanyInfo, LibraryInfo, Notification, PrintedCopy, PrintedCopyRequest, AdminNotification
)

# =====================================================
# CUSTOMER SERIALIZER (آمن)
# =====================================================

class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
            "account_type",
            "date_joined","is_staff", "is_superuser"
        ]
        read_only_fields = ["id", "account_type", "date_joined"]


# =====================================================
# CHANGE PASSWORD
# =====================================================

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("كلمتا المرور غير متطابقتين")
        return attrs


# =====================================================
# CATEGORY
# =====================================================

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


# =====================================================
# BOOK
# =====================================================

class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False
    )
    category_name = serializers.CharField(write_only=True, required=False)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "description",
            "category", "category_id", "category_name",
            "file", "cover",
            "views_count", "readings_count",
            "favorites_count", "download_count",
            "average_rating",
            "created_at", "created_by"
        ]

    def create(self, validated_data):
        category_name = validated_data.pop("category_name", None)
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)
            validated_data["category"] = category

        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user

        return super().create(validated_data)


# =====================================================
# DOWNLOAD
# =====================================================

class DownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Download
        fields = "__all__"


# =====================================================
# FAVORITE
# =====================================================



class FavoriteSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'book']

# =====================================================
# ANNOUNCEMENT
# =====================================================
class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        # ✨ فقط الحقول الموجودة في الموديل
        fields = ['id', 'title', 'content', 'image', 'created_at']
# =====================================================
# COMPANY INFO
# =====================================================
class CompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyInfo
        fields = "__all__"


# =====================================================
# CUSTOMER SERIALIZER
# =====================================================
class AdminNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNotification
        fields = ['id', 'title', 'message', 'is_read', 'recipient', 'created_at']
        read_only_fields = ['id', 'created_at', 'recipient']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'user', 'created_at']

# =====================================================
# LIBRARY INFO
# =====================================================

class LibraryInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryInfo
        fields = "__all__"
from .models import PrintedCopy

class PrintedCopySerializer(serializers.ModelSerializer):
    book_title = serializers.ReadOnlyField(source='book.title')

    class Meta:
        model = PrintedCopy
        fields = ['id', 'book', 'book_title', 'copy_number', 'status', 'added_at']
        read_only_fields = ['added_at']
from rest_framework import serializers
from .models import PrintedCopyRequest

class PrintedCopyRequestSerializer(serializers.ModelSerializer):
    book_title = serializers.ReadOnlyField(source="book.title")
    user_email = serializers.ReadOnlyField(source="user.email")
    user_address = serializers.ReadOnlyField(source="user.address")

    class Meta:
        model = PrintedCopyRequest
        fields = [
            "id",
            "book",
            "book_title",
            "user",
            "user_email",
            "user_address",
            "printed_copy",
            "status",
            "notes",
            "requested_at",
            "updated_at",
            "approved_at",
        ]
        read_only_fields = [
            "user",
            "status",
            "printed_copy",
            "approved_at",
        ]