# Generated by Django 2.2.2 on 2019-07-19 19:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0033_auto_20190718_1846'),
        ('adjuntos', '0007_identificacion_invalidada'),
        ('fiscales', '0002_auto_20190504_1938'),
        ('problemas', '0002_auto_20190511_1332'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problema',
            name='descripcion',
        ),
        migrations.RemoveField(
            model_name='problema',
            name='problema',
        ),
        migrations.RemoveField(
            model_name='problema',
            name='reportado_por',
        ),
        migrations.AddField(
            model_name='problema',
            name='attachment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='problemas', to='adjuntos.Attachment'),
        ),
        migrations.AlterField(
            model_name='problema',
            name='estado',
            field=models.CharField(blank=True, choices=[('potencial', 'potencial'), ('pendiente', 'pendiente'), ('en_curso', 'en_curso'), ('resuelto', 'resuelto')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='problema',
            name='mesa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='problemas', to='elecciones.Mesa'),
        ),
        migrations.AlterField(
            model_name='problema',
            name='resuelto_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ReporteDeProblema',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('tipo_de_problema', models.CharField(blank=True, choices=[('spam', 'Es SPAM'), ('invalida', 'Es inválida'), ('ilegible', 'No se entiende')], max_length=100, null=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('es_reporte_fake', models.BooleanField(default=False)),
                ('carga', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='problemas', to='elecciones.Carga')),
                ('identificacion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='problemas', to='adjuntos.Identificacion')),
                ('problema', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reportes', to='problemas.Problema')),
                ('reportado_por', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fiscales.Fiscal')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
