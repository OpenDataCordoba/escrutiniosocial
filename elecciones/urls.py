# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views, data_views
from fancy_cache import cache_page
from django.contrib.auth.decorators import login_required
from elecciones.resultados import Sumarizador

cached = cache_page(300)

urlpatterns = [
    url('^escuelas.geojson$', cached(
        views.LugaresVotacionGeoJSON.as_view()), name='geojson'),
    url('^escuelas/(?P<pk>\d+)$',
        views.EscuelaDetailView.as_view(), name='detalle_escuela'),
    url('^mapa/$', login_required(cached(views.Mapa.as_view())), name='mapa'),
    url(
        '^resultados/(?P<pk>\d+)?$',
        views.ResultadosCategoria.as_view(),
        name='resultados-categoria'
    ),
    url(
        '^mesas_circuito/(?P<pkcircuito>\d+)?/(?P<pkcategoria>\d+)?$',
        views.MesasDeCircuito.as_view(),
        name='mesas-circuito'
    ),
    url(r'^resultados-parciales-(?P<slug_categoria>[\w-]+).(?P<filetype>csv|xls)$',
        data_views.resultado_parcial_categoria, name='resultado-parcial-categoria'),

]
