# Generated by Django 5.0.1 on 2024-04-26 15:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0052_articulosmodel_precioventavendeedorexterno'),
    ]

    operations = [
        migrations.RenameField(
            model_name='articulosmodel',
            old_name='precioVentaVendeedorExterno',
            new_name='precioVentaVendedorExterno',
        ),
    ]