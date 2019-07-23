from elecciones.tests.factories import (
    AttachmentFactory,
    MesaFactory,
)
from django.urls import reverse
from elecciones.tests.test_resultados import fiscal_client, setup_groups # noqa
from http import HTTPStatus
from adjuntos.models import Attachment, Identificacion

def test_identificacion_create_view_get(fiscal_client):
    a = AttachmentFactory()
    response = fiscal_client.get(reverse('asignar-mesa', args=[a.id]))
    fotoUrl = a.foto.thumbnail['960x'].url
    assert response.status_code == HTTPStatus.OK
    assert fotoUrl in response.content.decode('utf8')

def test_identificacion_create_view_post(fiscal_client, admin_user):
    m1 = MesaFactory()
    a = AttachmentFactory()
    data = {
        'mesa': m1.id,
        'circuito': m1.circuito.id,
        'seccion': m1.circuito.seccion.id,
        'distrito': m1.circuito.seccion.distrito.id,
    }
    response = fiscal_client.post(reverse('asignar-mesa', args=[a.id]), data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse('siguiente-accion')
    assert a.identificaciones.count() == 1
    i = a.identificaciones.first()
    assert i.status == Identificacion.STATUS.identificada
    assert i.mesa == m1
    assert i.fiscal == admin_user.fiscal
    # la identificacion todavia no está consolidada
    a.refresh_from_db()
    assert a.identificacion_testigo is None
    assert not m1.attachments.exists()

def test_identificacion_create_view_get__desde_unidad_basica(fiscal_client):
    a = AttachmentFactory()
    response = fiscal_client.get(reverse('asignar-mesa-ub', args=[a.id]))
    assert response.status_code == HTTPStatus.OK

    foto_url = a.foto.thumbnail['960x'].url
    assert foto_url in response.content.decode('utf8')

def test_identificacion_create_view_post__desde_unidad_basica(fiscal_client):
    mesa_1 = MesaFactory()
    attachment = AttachmentFactory()
    data = {
        'mesa': mesa_1.id,
        'circuito': mesa_1.circuito.id,
        'seccion': mesa_1.circuito.seccion.id,
        'distrito': mesa_1.circuito.seccion.distrito.id,
    }
    response = fiscal_client.post(reverse('asignar-mesa-ub', args=[attachment.id]), data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse('procesar-acta-mesa', kwargs={'mesa_id': mesa_1.id})
    
    #refrescamos el attachment desde la base
    attachment.refresh_from_db()

    assert attachment.identificaciones.count() == 1
    assert attachment.status == Attachment.STATUS.identificada
    
    identificacion = attachment.identificaciones.first()
    assert attachment.identificacion_testigo == identificacion
    assert identificacion.status == Identificacion.STATUS.identificada
    assert identificacion.source == Identificacion.SOURCES.csv
    assert identificacion.mesa == mesa_1
    # la identificacion está consolidada, por lo tanto ya existe en la mesa
    assert mesa_1.attachments.exists()
    


def test_identificacion_problema_create_view_post(fiscal_client, admin_user):
    m1 = MesaFactory()
    a = AttachmentFactory()
    data = {
        'status': 'problema',
        'tipo_de_problema': 'invalida',
        'descripcion': 'Un problema'
    }
    response = fiscal_client.post(reverse('asignar-problema', args=[a.id]), data)
    assert response.status_code == 302
    assert response.url == reverse('siguiente-accion')
    assert a.identificaciones.count() == 1
    i = a.identificaciones.first()
    assert i.status == 'problema'
    assert i.fiscal == admin_user.fiscal
    assert i.mesa is None
    # mesa no tiene attach aun
    a.refresh_from_db()
    assert a.identificacion_testigo is None
    assert not m1.attachments.exists()