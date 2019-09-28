import pytest
from django.db import IntegrityError
from datetime import timedelta
from django.utils import timezone
from elecciones.tests.factories import (
    AttachmentFactory,
    FiscalFactory,
    IdentificacionFactory,
    MesaFactory,
)
from adjuntos.models import Attachment, Identificacion
from adjuntos.consolidacion import consumir_novedades_identificacion
from problemas.models import ReporteDeProblema, Problema


def test_attachment_unico(db):
    a = AttachmentFactory()
    assert a.foto
    assert a.foto_digest
    with pytest.raises(IntegrityError):
        AttachmentFactory(foto=a.foto)


def test_priorizadas_respeta_orden(db, settings):
    a1 = IdentificacionFactory(status='identificada').attachment
    a2 = IdentificacionFactory(status='spam').attachment
    a3 = IdentificacionFactory(status='spam').attachment
    assert set(Attachment.objects.sin_identificar()) == {a1, a2, a3}
    for i in range(settings.MIN_COINCIDENCIAS_IDENTIFICACION):
        a2.asignar_a_fiscal()
    for i in range(2 * settings.MIN_COINCIDENCIAS_IDENTIFICACION):
        a3.asignar_a_fiscal()
    # Me las debe entregar en orden.
    assert list(Attachment.objects.sin_identificar().priorizadas()) == [a1, a2, a3]

def test_priorizadas_ordena_por_cant_asignaciones_realizadas(db, settings):
    a1 = AttachmentFactory()
    a2 = AttachmentFactory()
    a3 = AttachmentFactory()
    assert a1.id < a2.id
    assert a2.id < a3.id
    assert set(Attachment.objects.sin_identificar()) == {a1, a2, a3}
    for i in range(settings.MIN_COINCIDENCIAS_IDENTIFICACION):
        a1.asignar_a_fiscal()
        a2.asignar_a_fiscal()
        a3.asignar_a_fiscal()

    # Prima el orden por id.
    assert list(Attachment.objects.sin_identificar().priorizadas()) == [a1, a2, a3]

    # Ahora a2 es devuelto.
    for i in range(settings.MIN_COINCIDENCIAS_IDENTIFICACION):
        a2.desasignar_a_fiscal()

    assert list(Attachment.objects.sin_identificar().priorizadas()) == [a2, a1, a3]

    # a2 es asignado nuevamente.
    for i in range(settings.MIN_COINCIDENCIAS_IDENTIFICACION):
        a2.asignar_a_fiscal()

    # Si bien a3 y a2 tienen la misma cantidad de asignaciones
    # vigentes, a2 fue asignado más veces. a1 y a3 empatan, salvo por id.
    assert list(Attachment.objects.sin_identificar().priorizadas()) == [a1, a3, a2]
    assert a1.cant_fiscales_asignados == a3.cant_fiscales_asignados
    assert a3.cant_fiscales_asignados == a2.cant_fiscales_asignados
    assert a3.cant_asignaciones_realizadas < a2.cant_asignaciones_realizadas


def test_sin_identificar_excluye_otros_estados(db):
    AttachmentFactory(status='spam')
    AttachmentFactory(status='invalida')
    AttachmentFactory(status='identificada')
    a = AttachmentFactory(status=Attachment.STATUS.sin_identificar)
    assert set(Attachment.objects.sin_identificar()) == {a}


def test_identificacion_status_count(db):
    a = AttachmentFactory()
    AttachmentFactory()    # no fecta
    m1 = MesaFactory()
    m2 = MesaFactory()
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)
    IdentificacionFactory(attachment=a, status='problema', mesa=None)
    IdentificacionFactory(attachment=a, status='problema', mesa=None)
    IdentificacionFactory(attachment=a, status='invalida', mesa=None)

    # un estado excepcional, pero eventualmente posible?
    IdentificacionFactory(attachment=a, status='problema', mesa=m1)

    IdentificacionFactory(attachment=a, status='identificada', mesa=m2)

    result = a.status_count(Identificacion.STATUS.identificada)
    assert sorted(result) == sorted([
        (m1.id, 1, 0),
        (m2.id, 1, 0),
    ])

    result = a.status_count(Identificacion.STATUS.problema)
    assert sorted(result) == sorted([
        (0, 2, 0),
        (m1.id, 1, 0)
    ])

def test_identificacion_consolidada_ninguno(db):
    a = AttachmentFactory()
    m1 = MesaFactory()
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)

    i1 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    f = FiscalFactory()
    Problema.reportar_problema(f, 'reporte 1',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.spam, identificacion=i1)
    assert i1.problemas.first().problema.estado == Problema.ESTADOS.potencial

    i2 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    Problema.reportar_problema(f, 'reporte 2',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.ilegible, identificacion=i2)

    assert a.identificacion_testigo is None

    cant_novedades = Identificacion.objects.filter(procesada=False).count()
    assert cant_novedades == 3
    consumir_novedades_identificacion()

    # Se consolidó un problema.
    assert i1.problemas.first().problema.estado == Problema.ESTADOS.pendiente

    cant_novedades = Identificacion.objects.filter(procesada=False).count()
    assert cant_novedades == 0

    assert a.identificacion_testigo is None


def test_identificacion_consolidada_alguna(db):
    a = AttachmentFactory()
    m1 = MesaFactory()
    i1 = IdentificacionFactory(attachment=a, status='identificada', mesa=m1)
    IdentificacionFactory(attachment=a, status='problema', mesa=None)
    i2 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    Problema.reportar_problema(FiscalFactory(), 'reporte 1',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.ilegible, identificacion=i2)
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)

    assert a.identificacion_testigo is None

    cant_novedades = Identificacion.objects.filter(procesada=False).count()
    assert cant_novedades == 4
    consumir_novedades_identificacion()

    # No se consolidó el problema.
    assert i2.problemas.first().problema.estado == Problema.ESTADOS.potencial

    cant_novedades = Identificacion.objects.filter(procesada=False).count()
    assert cant_novedades == 0

    a.refresh_from_db()
    assert a.identificacion_testigo == i1
    assert a.mesa == m1
    assert a.status == Attachment.STATUS.identificada


def test_identificacion_consolidada_con_minimo_1(db, settings):
    settings.MIN_COINCIDENCIAS_IDENTIFICACION = 1
    a = AttachmentFactory()
    m1 = MesaFactory()
    i1 = IdentificacionFactory(attachment=a, status='identificada', mesa=m1)
    consumir_novedades_identificacion()
    a.refresh_from_db()
    assert a.identificacion_testigo == i1
    assert a.mesa == m1
    assert a.status == Attachment.STATUS.identificada


def test_consolidador_marca_timeout(db, settings):
    a = AttachmentFactory()
    m1 = MesaFactory()
    i1 = IdentificacionFactory(attachment=a, status='identificada', mesa=m1)
    assert i1.tomada_por_consolidador is None
    consumir_novedades_identificacion()
    i1.refresh_from_db()
    assert i1.tomada_por_consolidador is not None
    assert i1.procesada is True


def test_consolidador_honra_timeout(db, settings):
    settings.MIN_COINCIDENCIAS_IDENTIFICACION = 1
    a = AttachmentFactory()
    m1 = MesaFactory()
    i1 = IdentificacionFactory(
        attachment=a, status='identificada', mesa=m1,
        tomada_por_consolidador=timezone.now() - timedelta(minutes=settings.TIMEOUT_CONSOLIDACION - 1)
    )
    consumir_novedades_identificacion()
    a.refresh_from_db()
    i1.refresh_from_db()
    # No la tomó aún.
    assert i1.procesada is False

    assert a.status == Attachment.STATUS.sin_identificar
    i1.tomada_por_consolidador = timezone.now() - timedelta(minutes=settings.TIMEOUT_CONSOLIDACION + 1)
    i1.save()
    consumir_novedades_identificacion()
    a.refresh_from_db()
    i1.refresh_from_db()

    # Ahora sí
    assert i1.procesada is True
    assert a.identificacion_testigo == i1
    assert a.mesa == m1
    assert a.status == Attachment.STATUS.identificada


def test_ciclo_de_vida_problemas_resolver(db):
    a = AttachmentFactory()
    m1 = MesaFactory()
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)

    # Está pendiente.
    assert a in Attachment.objects.sin_identificar()

    i1 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    f = FiscalFactory()
    Problema.reportar_problema(f, 'reporte 1',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.spam, identificacion=i1)
    assert i1.problemas.first().problema.estado == Problema.ESTADOS.potencial

    i2 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    Problema.reportar_problema(f, 'reporte 2',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.ilegible, identificacion=i2)

    assert i1.invalidada == False
    assert i2.invalidada == False

    consumir_novedades_identificacion()

    # Se consolidó un problema.
    a.refresh_from_db()
    assert a.status == Attachment.STATUS.problema
    problema = i1.problemas.first().problema
    assert problema.estado == Problema.ESTADOS.pendiente

    # El attach no está entre los pendientes.
    assert a not in Attachment.objects.sin_identificar()

    problema.resolver(FiscalFactory().user)

    assert problema.estado == Problema.ESTADOS.resuelto

    i1.refresh_from_db()
    i2.refresh_from_db()
    # Las identificaciones están invalidadas.
    assert i1.invalidada == True
    assert i2.invalidada == True

    consumir_novedades_identificacion()

    # Se agrega una nueva identificación y se consolida.
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)
    consumir_novedades_identificacion()
    a.refresh_from_db()
    assert a.status == Attachment.STATUS.identificada
    assert a.mesa == m1

def test_ciclo_de_vida_problemas_descartar(db):
    a = AttachmentFactory()
    m1 = MesaFactory()
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)

    i1 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    f = FiscalFactory()
    Problema.reportar_problema(f, 'reporte 1',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.spam, identificacion=i1)
    assert i1.problemas.first().problema.estado == Problema.ESTADOS.potencial

    i2 = IdentificacionFactory(attachment=a, status='problema', mesa=None)
    Problema.reportar_problema(f, 'reporte 2',
        ReporteDeProblema.TIPOS_DE_PROBLEMA.ilegible, identificacion=i2)

    assert i1.invalidada == False
    assert i2.invalidada == False

    consumir_novedades_identificacion()

    # Se consolidó un problema.
    a.refresh_from_db()
    assert a.status == Attachment.STATUS.problema
    problema = i1.problemas.first().problema
    assert problema.estado == Problema.ESTADOS.pendiente

    problema.descartar(FiscalFactory().user)

    assert problema.estado == Problema.ESTADOS.descartado

    i1.refresh_from_db()
    i2.refresh_from_db()
    # Las identificaciones están invalidadas.
    assert i1.invalidada == True
    assert i2.invalidada == True

    consumir_novedades_identificacion()

    # Se agrega una nueva identificación y se consolida.
    IdentificacionFactory(attachment=a, status='identificada', mesa=m1)
    consumir_novedades_identificacion()
    a.refresh_from_db()
    assert a.status == Attachment.STATUS.identificada
    assert a.mesa == m1
