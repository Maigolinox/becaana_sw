# Generated by Django 5.0.1 on 2024-01-28 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0004_delete_producto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='articulosmodel',
            name='urlArticulo',
            field=models.CharField(default='https://cdn.pixabay.com/photo/2022/12/29/17/14/candy-7685391_1280.png', max_length=200, verbose_name='URL de la imagen del artículo'),
        ),
    ]