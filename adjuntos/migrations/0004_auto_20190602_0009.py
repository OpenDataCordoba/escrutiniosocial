# Generated by Django 2.2.1 on 2019-06-02 03:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adjuntos', '0003_attachment_foto_digest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='email',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='adjuntos.Email'),
        ),
    ]