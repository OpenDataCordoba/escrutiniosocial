# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-01 14:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('fiscales', '0001_initial'),
        ('elecciones', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='votomesareportado',
            name='fiscal',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='fiscales.Fiscal'),
        ),
        migrations.AddField(
            model_name='votomesareportado',
            name='mesa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elecciones.Mesa'),
        ),
        migrations.AddField(
            model_name='votomesareportado',
            name='opcion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elecciones.Opcion'),
        ),
        migrations.AddField(
            model_name='opcion',
            name='partido',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opciones', to='elecciones.Partido'),
        ),
        migrations.AddField(
            model_name='mesa',
            name='circuito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elecciones.Circuito'),
        ),
        migrations.AddField(
            model_name='mesa',
            name='eleccion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elecciones.Eleccion'),
        ),
        migrations.AddField(
            model_name='mesa',
            name='lugar_votacion',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mesas', to='elecciones.LugarVotacion', verbose_name='Lugar de votacion'),
        ),
        migrations.AddField(
            model_name='lugarvotacion',
            name='circuito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='escuelas', to='elecciones.Circuito'),
        ),
        migrations.AddField(
            model_name='eleccion',
            name='opciones',
            field=models.ManyToManyField(related_name='elecciones', to='elecciones.Opcion'),
        ),
        migrations.AddField(
            model_name='circuito',
            name='referentes',
            field=models.ManyToManyField(blank=True, related_name='es_referente_de_circuito', to='fiscales.Fiscal'),
        ),
        migrations.AddField(
            model_name='circuito',
            name='seccion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elecciones.Seccion'),
        ),
        migrations.AddField(
            model_name='circuito',
            name='seccion_de_ponderacion',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='elecciones.AgrupacionPK'),
        ),
        migrations.AlterUniqueTogether(
            name='votomesareportado',
            unique_together=set([('mesa', 'opcion')]),
        ),
    ]