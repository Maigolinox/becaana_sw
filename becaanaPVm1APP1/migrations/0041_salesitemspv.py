# Generated by Django 5.0.1 on 2024-03-29 17:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0040_pvinventory'),
    ]

    operations = [
        migrations.CreateModel(
            name='salesItemsPV',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField(default=0)),
                ('qty', models.FloatField(default=0)),
                ('total', models.FloatField(default=0)),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='becaanaPVm1APP1.articulosmodel')),
                ('sale_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='becaanaPVm1APP1.sales')),
            ],
        ),
    ]