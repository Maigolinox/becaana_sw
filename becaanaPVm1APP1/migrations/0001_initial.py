# Generated by Django 5.0.1 on 2024-01-21 03:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='articulosModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombreArticulo', models.CharField(max_length=200, verbose_name='Nombre del artículo')),
                ('cantidadArticulo', models.IntegerField(verbose_name='Stock actual')),
                ('descripcionArticulo', models.TextField(max_length=400, verbose_name='Descripción del artículo')),
                ('costo', models.FloatField(verbose_name='Costo')),
                ('precioVentaPublico', models.FloatField(verbose_name='Precio de venta al público')),
                ('precioVentaProveedor', models.FloatField(verbose_name='Precio de venta al público')),
                ('cantidadMinima', models.FloatField(verbose_name='Cantidad mínima de producto')),
                ('cantidadMaxima', models.FloatField(verbose_name='Cantidad máxima de producto')),
            ],
        ),
        migrations.CreateModel(
            name='proveedoresModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombreProveedor', models.CharField(max_length=40, verbose_name='Nombre del Proveeedor')),
                ('apellidosProveedor', models.CharField(max_length=80, verbose_name='Apellidos del Proveedor')),
                ('direccionProveedor', models.CharField(max_length=80, verbose_name='Dirección del Proveedor')),
                ('telefonoProveedor', models.CharField(max_length=80, verbose_name='Dirección del Proveedor')),
                ('correoElectronicoProveedor', models.CharField(max_length=40, verbose_name='Correo electrónico del Proveedor')),
            ],
        ),
    ]