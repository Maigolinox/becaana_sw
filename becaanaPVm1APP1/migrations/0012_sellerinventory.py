# Generated by Django 5.0.1 on 2024-02-23 15:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0011_seller'),
    ]

    operations = [
        migrations.CreateModel(
            name='sellerInventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('precioVentaVendedor', models.FloatField(default=0)),
                ('qty', models.FloatField(default=0)),
                ('precioOriginal', models.FloatField(default=0)),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='becaanaPVm1APP1.articulosmodel')),
                ('seller_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='becaanaPVm1APP1.seller')),
            ],
        ),
    ]
