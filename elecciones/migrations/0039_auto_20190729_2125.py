# Generated by Django 2.2.2 on 2019-07-30 00:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0038_auto_20190729_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='mesacategoria',
            name='orden_de_llegada',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mesacategoria',
            name='percentil',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
