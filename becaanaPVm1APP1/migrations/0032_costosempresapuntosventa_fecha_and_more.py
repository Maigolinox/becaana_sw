# Generated by Django 5.0.1 on 2024-03-17 21:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0031_costosempresapuntosventa_costosempresavendedores'),
    ]

    operations = [
        migrations.AddField(
            model_name='costosempresapuntosventa',
            name='fecha',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name='costosempresavendedores',
            name='fecha',
            field=models.DateField(default=datetime.date.today),
        ),
    ]