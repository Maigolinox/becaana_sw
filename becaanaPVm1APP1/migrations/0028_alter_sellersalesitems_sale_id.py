# Generated by Django 5.0.1 on 2024-02-25 18:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0027_remove_sales_origen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sellersalesitems',
            name='sale_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='becaanaPVm1APP1.sellersales'),
        ),
    ]
