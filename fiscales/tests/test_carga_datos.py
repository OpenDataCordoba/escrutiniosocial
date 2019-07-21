import pytest
from django.urls import reverse
from elecciones.tests.factories import (
    CargaFactory,
    CategoriaFactory,
    CategoriaOpcionFactory,
    CircuitoFactory,
    IdentificacionFactory,
    MesaCategoriaFactory,
    MesaFactory,
    OpcionFactory,
    VotoMesaReportadoFactory,
)
from elecciones.tests.test_resultados import fiscal_client, setup_groups    # noqa
from elecciones.models import Carga, MesaCategoria, Opcion
from adjuntos.models import Identificacion
from adjuntos.consolidacion import consumir_novedades_identificacion, consumir_novedades_carga

from elecciones.tests.test_models import consumir_novedades_y_actualizar_objetos


def test_elegir_acta_sin_mesas(fiscal_client):
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert 'No hay actas para cargar por el momento' in response.content.decode('utf8')


def test_siguiente_redirige_a_cargar_resultados(db, fiscal_client):
    c1 = CategoriaFactory()
    c2 = CategoriaFactory()
    m1 = MesaFactory(categorias=[c1])
    IdentificacionFactory(
        mesa=m1,
        status='identificada',
        source=Identificacion.SOURCES.csv,
    )
    m2 = MesaFactory(categorias=[c1, c2])
    assert MesaCategoria.objects.count() == 3
    IdentificacionFactory(
        mesa=m2,
        status='identificada',
        source=Identificacion.SOURCES.csv,
    )
    # ambas consolidadas via csv
    consumir_novedades_identificacion()
    m1c1 = MesaCategoria.objects.get(mesa=m1, categoria=c1)
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('carga-total', args=[m1c1.id])

    # como m1c1 queda en periodo de "taken" (aunque no se haya ocupado aún)
    # se pasa a la siguiente mesacategoria
    m2c1 = MesaCategoria.objects.get(mesa=m2, categoria=c1)

    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('carga-total', args=[m2c1.id])

    # ahora la tercera
    m2c2 = MesaCategoria.objects.get(mesa=m2, categoria=c2)
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('carga-total', args=[m2c2.id])

    # ya no hay actas (todas en taken)
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 200   # no hay actas

    # se libera una. pero no se alcanza a completar
    m2c2.release()
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('carga-total', args=[m2c2.id])


@pytest.mark.parametrize('status, parcial', [
    (MesaCategoria.STATUS.sin_cargar, True),
    (MesaCategoria.STATUS.parcial_sin_consolidar, True),
    (MesaCategoria.STATUS.parcial_en_conflicto, True),
    (MesaCategoria.STATUS.parcial_consolidada_csv, True),      # ASK: hace falta si es csv?
    (MesaCategoria.STATUS.parcial_consolidada_dc, False),
    (MesaCategoria.STATUS.total_sin_consolidar, False),
    (MesaCategoria.STATUS.total_en_conflicto, False),
    (MesaCategoria.STATUS.total_consolidada_csv, False),
])
def test_cargar_resultados_redirige_a_parcial_si_es_necesario(db, fiscal_client, status, parcial):
    c1 = CategoriaFactory(requiere_cargas_parciales=True)
    m1c1 = MesaCategoriaFactory(categoria=c1, orden_de_carga=0.1, status=status)
    response = fiscal_client.get(reverse('siguiente-accion'))
    assert response.status_code == 302
    assert response.url == reverse('carga-parcial' if parcial else 'carga-total', args=[m1c1.id])


def test_formset_en_carga_parcial_solo_muestra_prioritarias(db, fiscal_client):
    c = CategoriaFactory()
    o = CategoriaOpcionFactory(categoria=c, prioritaria=True).opcion

    # la opcion 2 no se muestr
    CategoriaOpcionFactory(categoria=c, prioritaria=False).opcion
    mc = MesaCategoriaFactory(categoria=c)
    parciales = reverse(
        'carga-parcial', args=[mc.id]
    )
    response = fiscal_client.get(parciales)
    assert len(response.context['formset']) == 1
    response.context['formset'][0].fields['opcion'].choices == [
        (o.id, str(o))
    ]


def test_formset_en_carga_total_muestra_todos(db, fiscal_client):
    c = CategoriaFactory(id=100, opciones=[])
    o = CategoriaOpcionFactory(categoria=c, opcion__orden=3, prioritaria=True).opcion
    o2 = CategoriaOpcionFactory(categoria=c, opcion__orden=1, prioritaria=False).opcion
    mc = MesaCategoriaFactory(categoria=c)
    totales = reverse(
        'carga-total', args=[mc.id]
    )
    response = fiscal_client.get(totales)
    assert len(response.context['formset']) == 2
    response.context['formset'][0].fields['opcion'].choices == [
        (o2.id, str(o2)),
        (o.id, str(o))
    ]


def test_formset_en_carga_total_reusa_parcial_confirmada(db, fiscal_client, settings):
    # solo una carga, para simplificar el setup
    settings.MIN_COINCIDENCIAS_CARGAS = 1

    c = CategoriaFactory(id=100, opciones=[])
    # notar que el orden no coincide con el id

    o1 = CategoriaOpcionFactory(categoria=c, opcion__orden=3, prioritaria=True).opcion
    o2 = CategoriaOpcionFactory(categoria=c, opcion__orden=1, prioritaria=False).opcion
    o3 = CategoriaOpcionFactory(categoria=c, opcion__orden=2, prioritaria=False).opcion
    o4 = CategoriaOpcionFactory(categoria=c, opcion__orden=4, prioritaria=True).opcion

    mc = MesaCategoriaFactory(categoria=c)

    # se carga parcialente, la opcion prioritaira "o"
    carga = CargaFactory(mesa_categoria=mc, tipo='parcial')
    VotoMesaReportadoFactory(carga=carga, opcion=o1, votos=10)
    VotoMesaReportadoFactory(carga=carga, opcion=o4, votos=3)

    # consolidamos.
    consumir_novedades_carga()
    mc.refresh_from_db()
    assert mc.status == MesaCategoria.STATUS.parcial_consolidada_dc
    assert mc.carga_testigo == carga
    assert set(carga.opcion_votos()) == {(o1.id, 10), (o4.id, 3)}

    # ahora pedimos la carga total
    totales = reverse(
        'carga-total', args=[mc.id]
    )
    response = fiscal_client.get(totales)

    # tenemos las tres opciones en orden
    assert len(response.context['formset']) == 4
    assert response.context['formset'][0].initial['opcion'] == o2
    assert response.context['formset'][1].initial['opcion'] == o3
    assert response.context['formset'][2].initial['opcion'] == o1
    assert response.context['formset'][3].initial['opcion'] == o4

    # y los valores de los votos
    assert response.context['formset'][0].initial['votos'] is None
    assert response.context['formset'][1].initial['votos'] is None
    assert response.context['formset'][2].initial['votos'] == 10
    assert response.context['formset'][3].initial['votos'] == 3

    # el valor previo es readonly
    assert response.context['formset'][2].fields['votos'].widget.attrs['readonly'] is True
    assert response.context['formset'][3].fields['votos'].widget.attrs['readonly'] is True


def test_formset_reusa_metadata(db, fiscal_client):
    # hay una categoria con una opcion metadata ya consolidada
    o1 = OpcionFactory(tipo=Opcion.TIPOS.metadata, orden=1)
    cat1 = CategoriaFactory(opciones=[o1])
    mc = MesaCategoriaFactory(categoria=cat1, status=MesaCategoria.STATUS.total_consolidada_dc)
    carga = CargaFactory(mesa_categoria=mc, tipo='identificada')
    VotoMesaReportadoFactory(carga=carga, opcion=o1, votos=10)

    # otra categoria incluye la misma metadata.
    o2 = OpcionFactory(orden=2)
    cat2 = CategoriaFactory(opciones=[o1, o2])
    mc2 = MesaCategoriaFactory(categoria=cat2, mesa=mc.mesa)

    response = fiscal_client.get(reverse('carga-total', args=[mc2.id]))
    assert len(response.context['formset']) == 2
    assert response.context['formset'][0].initial['opcion'] == o1
    assert response.context['formset'][1].initial['opcion'] == o2

    # y los valores de los votos
    assert response.context['formset'][0].initial['votos'] == 10
    assert response.context['formset'][0].fields['votos'].widget.attrs['readonly'] is True

    assert response.context['formset'][1].initial['votos'] is None


def test_detalle_mesa_categoria(db, fiscal_client):
    opcs = OpcionFactory.create_batch(3)
    e1 = CategoriaFactory(opciones=opcs)
    e2 = CategoriaFactory(opciones=opcs)
    mesa = MesaFactory(categorias=[e1, e2])
    c1 = CargaFactory(
            mesa_categoria__mesa=mesa,
            mesa_categoria__categoria=e1,
            tipo=Carga.TIPOS.parcial,
            origen=Carga.SOURCES.csv
    )
    mc = c1.mesa_categoria
    votos1 = VotoMesaReportadoFactory(
        opcion=opcs[0],
        votos=1,
        carga=c1,
    )
    votos2 = VotoMesaReportadoFactory(
        opcion=opcs[1],
        votos=2,
        carga=c1,
    )
    votos3 = VotoMesaReportadoFactory(
        opcion=opcs[2],
        votos=1,
        carga=c1,
    )

    # a otra carga
    vm = VotoMesaReportadoFactory(
        opcion=opcs[2],
        votos=1
    )
    c1.actualizar_firma()
    consumir_novedades_y_actualizar_objetos([mc])
    assert mc.carga_testigo == c1
    url = reverse('detalle-mesa-categoria', args=[e1.id, mesa.numero])
    response = fiscal_client.get(url)

    assert list(response.context['reportados']) == [votos1, votos2, votos3]
