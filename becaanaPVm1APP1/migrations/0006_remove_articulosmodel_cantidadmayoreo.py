# Generated by Django 5.0.1 on 2024-01-28 19:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0005_articulosmodel_urlarticulo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articulosmodel',
            name='cantidadMayoreo',
        ),
    ]
