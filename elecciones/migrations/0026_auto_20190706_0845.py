# Generated by Django 2.2.1 on 2019-07-06 11:45

from django.db import migrations, models
import django.db.models.deletion


def crear_distrito_unico(apps, schema_editor):
    Distrito = apps.get_model("elecciones", "Distrito")         # noqa
    Distrito.objects.create(numero='1', nombre='Distrito único')


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0025_auto_20190704_1639'),
    ]

    operations = [
        migrations.CreateModel(
            name='Distrito',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(null=True)),
                ('nombre', models.CharField(max_length=100)),
                ('electores', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Distrito electoral',
                'verbose_name_plural': 'Distrito electorales',
            },
        ),
        migrations.RunPython(crear_distrito_unico),

        migrations.AddField(
            model_name='seccion',
            name='distrito',
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.CASCADE, to='elecciones.Distrito'
            ),
            preserve_default=False,
        ),
    ]
