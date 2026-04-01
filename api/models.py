from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator


# =====================================================
# USER
# =====================================================

class Customer(AbstractUser):
    ACCOUNT_TYPES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default='customer'
    )

    reset_code = models.CharField(max_length=6, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


# =====================================================
# CATEGORY
# =====================================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =====================================================
# BOOK
# =====================================================

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="books"
    )

    file = models.FileField(upload_to="books/")
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)

    views_count = models.PositiveIntegerField(default=0)
    readings_count = models.PositiveIntegerField(default=0)
    favorites_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    average_rating = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_books"
    )

    def update_rating(self):
        avg = self.ratings.aggregate(avg=Avg("value"))["avg"]
        self.average_rating = avg or 0
        self.save(update_fields=["average_rating"])

    def __str__(self):
        return self.title


# =====================================================
# VIEW
# =====================================================

class View(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="views")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["book"]),
            models.Index(fields=["user"]),
        ]


# =====================================================
# READING
# =====================================================

class Reading(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="readings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="readings")
    started_at = models.DateTimeField(auto_now_add=True)


# =====================================================
# DOWNLOAD
# =====================================================

class Download(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="downloads")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="downloads")
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')


# =====================================================
# FAVORITE
# =====================================================

class Favorite(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="favorites")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')


# =====================================================
# RATING
# =====================================================

class Rating(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="ratings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="ratings")
    value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')


# =====================================================
# ANNOUNCEMENT
# =====================================================
from django.conf import settings
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="announcements/", blank=True, null=True)  # ✅
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# =====================================================
# COMPANY INFO
# =====================================================

class CompanyInfo(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="company_logo/", blank=True, null=True)

    def __str__(self):
        return self.name


# =====================================================
# LIBRARY INFO
# =====================================================

class LibraryInfo(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="library_logo/", blank=True, null=True)

    def __str__(self):
        return self.name
# =====================================================
# PRINTED COPY
# =====================================================

class PrintedCopy(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('reserved', 'Reserved'),
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="printed_copies"
    )
    copy_number = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.book.title} - Copy {self.copy_number} ({self.status})"

    class Meta:
        unique_together = ('book', 'copy_number')
        indexes = [
            models.Index(fields=['book']),
            models.Index(fields=['status']),
        ]
# =====================================================
# PRINTED COPY REQUEST
# =====================================================

class PrintedCopyRequest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="print_requests"
    )

    user = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="print_requests"
    )

    printed_copy = models.ForeignKey(
        PrintedCopy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    notes = models.TextField(blank=True, null=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    approved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.book.title} ({self.status})"

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['book']),
            models.Index(fields=['user']),
        ]
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
User = get_user_model()
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
class Notification(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class AdminNotification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_notifications",
        null=True,  # null يعني إشعار عام إذا لم يكن مخصص لمستخدم محدد
        blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        target = self.recipient.email if self.recipient else "All Admins"
        return f"{self.title} -> {target}"