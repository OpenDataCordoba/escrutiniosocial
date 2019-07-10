from django.urls import reverse
from elecciones.tests.factories import (
    VotoMesaReportadoFactory,
    CategoriaFactory,
    AttachmentFactory,
    MesaFactory,
    OpcionFactory,
    CircuitoFactory,
    CargaFactory,
)
from elecciones.models import Mesa, VotoMesaReportado, MesaCategoria
from elecciones.tests.test_resultados import fiscal_client          # noqa


def test_elegir_acta_sin_mesas(fiscal_client):
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert 'No hay actas para cargar por el momento' in response.content.decode('utf8')


def test_elegir_acta_mesas_redirige(db, fiscal_client):
    assert Mesa.objects.count() == 0
    assert VotoMesaReportado.objects.count() == 0
    c = CircuitoFactory(id = 100001)
    e1 = CategoriaFactory()
    e2 = CategoriaFactory()

    m1 = AttachmentFactory(mesa__categoria=[e1], mesa__lugar_votacion__circuito=c).mesa
    e2 = CategoriaFactory()
    m2 = AttachmentFactory(mesa__categoria=[e1, e2], mesa__lugar_votacion__circuito=c).mesa

    assert m1.orden_de_carga == 1
    assert m2.orden_de_carga == 2

    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m1.numero])

    # como m1 queda en periodo de "taken" (aunque no se haya ocupado aun)
    # se pasa a la siguiente mesa
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m2.numero])

    # se carga esa categoria
    VotoMesaReportadoFactory(
        carga__mesa=m2,
        carga__categoria=e1,
        opcion=e1.opciones.first(),
        votos=1
    )

    # FIX ME . El periodo de taken deberia ser *por categoria*.
    # en este escenario donde esta lockeado la mesa para la categoria 1, pero no se está
    # cargando la mesa 2, un dataentry queda idle
    # ...
    # Esto cambio, ahora la siguiente accion es chequear una categoria
    # Carlos Lombardi, 2019.07.09
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('chequear-resultado-mesa', args=[e1.id, m2.numero])

    m2.taken = None
    m2.save()
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e2.id, m2.numero])


def test_elegir_acta_prioriza_por_tamaño_circuito(db, fiscal_client):
    e1 = CategoriaFactory()

    m1 = AttachmentFactory(mesa__categoria=[e1]).mesa
    m2 = AttachmentFactory(mesa__categoria=[e1]).mesa
    m3 = AttachmentFactory(mesa__categoria=[e1]).mesa
    # creo otras mesas asociadas a los circuitos
    c1 = m1.lugar_votacion.circuito
    c2 = m2.lugar_votacion.circuito
    c3 = m3.lugar_votacion.circuito

    MesaFactory.create_batch(
        3,
        categoria=[e1],
        lugar_votacion__circuito=c1
    )
    MesaFactory.create_batch(
        10,
        categoria=[e1],
        lugar_votacion__circuito=c2
    )
    MesaFactory.create_batch(
        5,
        categoria=[e1],
        lugar_votacion__circuito=c3
    )
    assert c1.electores == 400
    assert c2.electores == 1100
    assert c3.electores == 600
    assert m1.orden_de_carga == m2.orden_de_carga == m3.orden_de_carga == 1
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m2.numero])
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m3.numero])
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m1.numero])


def test_carga_mesa_redirige_a_siguiente(db, fiscal_client):
    o = OpcionFactory(es_contable=True)
    o2 = OpcionFactory(es_contable=False)
    e1 = CategoriaFactory(opciones=[o, o2])
    e2 = CategoriaFactory(opciones=[o])
    m1 = AttachmentFactory(mesa__categoria=[e1, e2]).mesa

    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.url == reverse('mesa-cargar-resultados', args=[e1.id, m1.numero])

    # formset para categoria e1 arranca en blanco
    url = response.url
    response = fiscal_client.get(response.url)
    formset = response.context['formset']
    assert len(formset) == 2
    assert formset[0].initial == {'opcion': o}
    assert formset[1].initial == {'opcion': o2}

    # response = fiscal_client.get(url)
    response = fiscal_client.post(url, {
        'form-0-opcion': str(o.id),
        'form-0-votos': str(m1.electores // 2),
        'form-1-opcion': str(o2.id),
        'form-1-votos': str(m1.electores // 2),
        'form-TOTAL_FORMS': '2',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '2',
        'form-MAX_NUM_FORMS': '1000',
    })
    assert response.status_code == 302
    assert response.url == reverse('post-cargar-resultados', args=[m1.numero, e1.nombre])
    # en rigor, aca habria que probar que al "pulsar" el boton de post-cargar-resultados,
    # aparece la siguiente categoria de la misma acta
    # igualmente esta logica debería cambiar en breve
    # por la misma razon, el resto del test no tiene sentido
    # Carlos Lombardi, 2019.7.9

    # el form de la nueva categoria e2 está en blanco
    # url = response.url
    # response = fiscal_client.get(response.url)
    # formset = response.context['formset']
    # assert len(formset) == 1
    # assert formset[0].initial == {'opcion': o}

    # # si completamos y es valido, no quedan
    # # categorias por cargar y pide otra acta
    # response = fiscal_client.post(url, {
    #     'form-0-opcion': str(o.id),
    #     'form-0-votos': str(m1.electores),
    #     'form-TOTAL_FORMS': '1',
    #     'form-INITIAL_FORMS': '0',
    #     'form-MIN_NUM_FORMS': '1',
    #     'form-MAX_NUM_FORMS': '1000',
    # })
    # assert response.status_code == 302
    # assert response.url == reverse('post-cargar-resultados', args=[m1.numero, e2.nombre])




def test_chequear_resultado(db, fiscal_client):
    o = OpcionFactory(es_contable=True)
    e1 = CategoriaFactory(opciones=[o])
    mesa = MesaFactory(categoria=[e1])
    me = MesaCategoria.objects.get(categoria=e1, mesa=mesa)
    assert me.confirmada is False

    VotoMesaReportadoFactory(opcion=o, carga__mesa=mesa, carga__categoria=e1, votos=1)
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('chequear-resultado-mesa', args=[e1.id, mesa.numero])
    me.confirmada = True
    me.save()
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 200
    assert 'No hay actas para cargar por el momento' in response.content.decode('utf8')


def test_chequear_resultado_mesa(db, fiscal_client):
    opcs = OpcionFactory.create_batch(3, es_contable=True)
    e1 = CategoriaFactory(opciones=opcs)
    e2 = CategoriaFactory(opciones=opcs)
    mesa = MesaFactory(categoria=[e1, e2])
    me = MesaCategoria.objects.get(categoria=e1, mesa=mesa)
    assert me.confirmada is False
    votos1 = VotoMesaReportadoFactory(opcion=opcs[0], carga__mesa=mesa, carga__categoria=e1, votos=1)
    votos2 = VotoMesaReportadoFactory(opcion=opcs[1], carga__mesa=mesa, carga__categoria=e1, votos=2)
    votos3 = VotoMesaReportadoFactory(opcion=opcs[2], carga__mesa=mesa, carga__categoria=e1, votos=1)

    # a otra categoria
    VotoMesaReportadoFactory(opcion=opcs[2], carga__mesa=mesa, carga__categoria=e2, votos=1)

    url = reverse('chequear-resultado-mesa', args=[e1.id, mesa.numero])
    response = fiscal_client.get(url)

    assert list(response.context['reportados']) == [votos1, votos2, votos3]

    response = fiscal_client.post(url, {'confirmar': 'confirmar'})
    assert response.status_code == 302
    assert response.url == reverse('post-confirmar-resultados', args=[mesa.numero])
    me.refresh_from_db()
    assert me.confirmada is True


def test_chequear_resultado_categoria_desactivada(db, fiscal_client):
    opcs = OpcionFactory.create_batch(3, es_contable=True)
    e1 = CategoriaFactory(opciones=opcs)
    assert e1.activa is True
    mesa = MesaFactory(categoria=[e1])
    # existe una carga para esa categoria / mesa
    CargaFactory(mesa=mesa, categoria=e1)
    url = reverse('chequear-resultado-mesa', args=[e1.id, mesa.numero])
    response = fiscal_client.get(url)
    assert response.status_code == 200
    e1.activa = False
    e1.save()
    response = fiscal_client.get(url)
    assert response.status_code == 404

