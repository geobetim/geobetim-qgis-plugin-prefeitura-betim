"""Pré-requisitos de camada e leitura para memória.

Os algoritmos do conjunto pressupõem a camada de trechos **inteira** carregada no
projeto: percorrem todas as feições de linha uma vez, guardam geometria e código
por id, agrupam ids por `COD_LOGRADOURO` e montam um ``QgsSpatialIndex``.

O cálculo é planar e as tolerâncias são em metros, então a camada precisa estar
num CRS projetado com unidade em metros.
"""

from collections import defaultdict

from qgis.core import NULL, QgsProcessingException, QgsSpatialIndex, QgsUnitTypes


def _nulo(valor):
    return valor is None or valor == NULL


def exigir_crs_metrico(camada):
    """Levanta ``QgsProcessingException`` se a camada não estiver em CRS métrico."""
    crs = camada.crs()
    if crs.isGeographic() or crs.mapUnits() != QgsUnitTypes.DistanceMeters:
        raise QgsProcessingException(
            "A camada precisa estar em um CRS projetado com unidade em metros. "
            "Reprojete antes de rodar (as tolerâncias são em metros e o cálculo "
            "é planar)."
        )


class LeituraDaCamada:
    """Resultado de ``ler_camada``: dicionários indexados pelo id da feição."""

    def __init__(
        self,
        geom_por_id,
        cod_por_id,
        por_codigo,
        indice_espacial,
        valor_extra,
        sem_codigo=0,
    ):
        self.geom_por_id = geom_por_id  # id -> QgsGeometry
        self.cod_por_id = cod_por_id  # id -> valor do campo de agrupamento
        self.por_codigo = por_codigo  # cod -> list[id]
        self.indice_espacial = indice_espacial  # QgsSpatialIndex das feições
        self.valor_extra = valor_extra  # nome_campo -> {id -> valor}
        self.sem_codigo = sem_codigo  # feições desconsideradas por código nulo


def ler_camada(camada, nome_campo_codigo, campos_extra=(), feedback=None):
    """Lê todas as feições da camada para memória.

    ``campos_extra`` — nomes de campos adicionais cujos valores por feição também
    são recolhidos (ex.: o atributo do número sequencial, para a numeração
    decidir o que já foi numerado).

    Feição com o atributo de agrupamento **nulo** não pertence a logradouro
    nenhum: é desconsiderada por completo — fora dos dicionários e do índice
    espacial, logo fora de escopo e fora do grafo (não vira cruzamento). A
    contagem fica em ``sem_codigo`` para o algoritmo avisar.
    """
    geom_por_id = {}
    cod_por_id = {}
    por_codigo = defaultdict(list)
    indice_espacial = QgsSpatialIndex()
    valor_extra = {nome: {} for nome in campos_extra}
    sem_codigo = 0

    for f in camada.getFeatures():
        if feedback is not None and feedback.isCanceled():
            break
        cod = f[nome_campo_codigo]
        if _nulo(cod):
            sem_codigo += 1
            continue
        fid = f.id()
        g = f.geometry()
        geom_por_id[fid] = g
        cod_por_id[fid] = cod
        por_codigo[cod].append(fid)
        indice_espacial.addFeature(fid, g.boundingBox())
        for nome in campos_extra:
            valor_extra[nome][fid] = f[nome]

    return LeituraDaCamada(
        geom_por_id, cod_por_id, por_codigo, indice_espacial, valor_extra, sem_codigo
    )


def avisar_sem_codigo(leitura, feedback):
    """Aviso padrão quando a leitura desconsiderou feições sem código."""
    if leitura.sem_codigo:
        feedback.pushWarning(
            "{0} trecho(s) com o atributo de agrupamento nulo foram "
            "desconsiderados (não pertencem a logradouro nenhum).".format(
                leitura.sem_codigo
            )
        )
