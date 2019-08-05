# Generated by Django 2.2.2 on 2019-07-29 15:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fiscales', '0004_auto_20190727_1136'),
        ('adjuntos', '0009_merge_20190727_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='taken_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='fiscales.Fiscal'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='taken',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]