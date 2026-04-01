from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book, Favorite, Download, PrintedCopyRequest, Notification, AdminNotification
from django.contrib.auth import get_user_model

User = get_user_model()

# =====================================================
# إشعار عند إضافة كتاب جديد
# =====================================================
@receiver(post_save, sender=Book)
def book_created_notification(sender, instance, created, **kwargs):
    if created and instance.created_by:
        # إشعار للعميل الذي أضاف الكتاب
        Notification.objects.create(
            user=instance.created_by,  # بدل recipient
            title="تمت إضافة كتاب جديد",
            message=f"لقد أضفت كتاب '{instance.title}' بنجاح."
        )
        # إشعار لجميع المشرفين (AdminNotification)
        admins = User.objects.filter(account_type='admin')
        for admin in admins:
            AdminNotification.objects.create(
                recipient=admin,
                title="كتاب جديد مضاف",
                message=f"قام {instance.created_by.email} بإضافة كتاب جديد: '{instance.title}'"
            )

# =====================================================
# إشعار عند إضافة كتاب للمفضلة
# =====================================================
@receiver(post_save, sender=Favorite)
def favorite_notification(sender, instance, created, **kwargs):
    if created and instance.book.created_by:
        Notification.objects.create(
            user=instance.book.created_by,  # بدل recipient
            title="تمت إضافة كتابك للمفضلة",
            message=f"{instance.user.email} أضاف كتابك '{instance.book.title}' إلى المفضلة."
        )

# =====================================================
# إشعار عند تنزيل كتاب
# =====================================================
@receiver(post_save, sender=Download)
def download_notification(sender, instance, created, **kwargs):
    if created and instance.book.created_by:
        Notification.objects.create(
            user=instance.book.created_by,  # بدل recipient
            title="تم تنزيل كتابك",
            message=f"{instance.user.email} قام بتنزيل كتابك '{instance.book.title}'."
        )

# =====================================================
# إشعار عند طلب نسخة مطبوعة
# =====================================================
@receiver(post_save, sender=PrintedCopyRequest)
def printed_copy_request_notification(sender, instance, created, **kwargs):
    if created:
        # إشعار للمشرفين
        admins = User.objects.filter(account_type='admin')
        for admin in admins:
            AdminNotification.objects.create(
                recipient=admin,
                title="طلب نسخة مطبوعة جديدة",
                message=f"{instance.user.email} طلب نسخة مطبوعة من الكتاب '{instance.book.title}'."
            )
    else:
        # إشعار للمستخدم عند تحديث الحالة
        Notification.objects.create(
            user=instance.user,  # بدل recipient
            title="تحديث حالة طلب النسخة المطبوعة",
            message=f"حالة طلبك للكتاب '{instance.book.title}' تغيرت إلى '{instance.status}'."
        )