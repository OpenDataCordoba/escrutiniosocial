# Generated by Django 2.2.2 on 2019-07-22 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0034_auto_20190721_2211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distrito',
            name='numero',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='seccion',
            name='numero',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
