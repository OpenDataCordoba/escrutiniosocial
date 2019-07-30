# Generated by Django 2.2.2 on 2019-07-27 14:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0037_auto_20190727_1136'),
        ('fiscales', '0003_fiscal_troll'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiscal',
            name='referido_codigo',
            field=models.CharField(blank=True, max_length=4, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='fiscal',
            name='referido_por_apellido',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='fiscal',
            name='referido_por_codigo',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='fiscal',
            name='referido_por_nombres',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='fiscal',
            name='seccion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fiscal', to='elecciones.Seccion'),
        ),
    ]
