# Generated by Django 5.0.1 on 2024-03-28 22:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0036_alter_sellerinventory_seller_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='costosempresavendedoresmodel',
            name='vendedor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Nombre del vendedor al que se le dá'),
        ),
    ]