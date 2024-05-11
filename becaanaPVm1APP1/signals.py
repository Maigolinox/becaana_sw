from django.db.models import signals
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import usersPermission

@receiver(signals.post_save, sender = User)
def create_customer(sender, instance, created, *args, **kwargs):
    if created:
        usersPermission.objects.create(user=instance)
