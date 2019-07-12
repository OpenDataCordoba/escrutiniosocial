from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.elegir_adjunto, name="elegir-adjunto"),
    url(r'^(?P<attachment_id>\d+)/$', views.IdentificacionCreateView.as_view(), name='asignar-mesa'),
    url(r'^(?P<attachment_id>\d+)/problema$', views.IdentificacionProblemaCreateView.as_view(), name='asignar-problema'),
    url(r'^(?P<attachment_id>\d+)/editar-foto$', views.editar_foto, name='editar-foto'),
    url(r'^agregar$', views.AgregarAdjuntos.as_view(), name="agregar-adjuntos"),
    url(r'^agregar-ub$', views.AgregarAdjuntosDesdeUnidadBasica.as_view(), name="agregar-adjuntos-ub"),
]
