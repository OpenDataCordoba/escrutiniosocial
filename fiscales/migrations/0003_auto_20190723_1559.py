# Generated by Django 2.2.2 on 2019-07-23 18:59

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0039_auto_20190723_1559'),
        ('fiscales', '0002_auto_20190504_1938'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiscal',
            name='referido_codigo',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name='fiscal',
            name='referido_por_codigo',
            field=models.UUIDField(blank=True, null=True),
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
