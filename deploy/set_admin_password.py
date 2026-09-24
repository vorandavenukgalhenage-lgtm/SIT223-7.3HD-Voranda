import os
from django.contrib.auth import get_user_model

User = get_user_model()
password = os.environ.get("ADMIN_PASSWORD")
admin = User.objects.filter(email="admin@example.com").first()
if password and admin:
    admin.set_password(password)
    admin.save()
    print("Admin password rotated from environment")
else:
    print("Admin password NOT rotated")