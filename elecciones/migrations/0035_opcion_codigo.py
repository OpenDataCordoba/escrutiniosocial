# Generated by Django 2.2.2 on 2019-07-14 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0034_auto_20190721_2211'),
    ]

    operations = [
        migrations.AddField(
            model_name='opcion',
            name='codigo',
            field=models.CharField(blank=True, help_text='Codigo de opción', max_length=10, null=True),
        ),
    ]
