# Generated by Django 5.0.1 on 2024-03-02 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('becaanaPVm1APP1', '0028_alter_sellersalesitems_sale_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='sales',
            name='origin',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]