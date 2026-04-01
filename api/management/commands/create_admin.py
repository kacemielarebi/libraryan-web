from django.core.management.base import BaseCommand
from api.models import Customer  # ضع اسم التطبيق الصحيح

class Command(BaseCommand):
    help = 'Creates default admin user'

    def handle(self, *args, **kwargs):
        admin_user, created = Customer.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin',
                'account_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'phone': '+213123456789',
                'address': 'العنوان الإداري'
            }
        )

        admin_user.set_password('Admin123!@#')
        admin_user.save()

        self.stdout.write(self.style.SUCCESS(f'Admin created: {created}'))