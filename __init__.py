"""Plugin do QGIS: conjunto de algoritmos da Prefeitura de Betim.

Um único provider do Processing ("Prefeitura de Betim") reúne os algoritmos de
edição da camada de trechos-logradouros, agrupados por escopo ("Trecho
logradouro").

Ponto de entrada exigido pelo QGIS: ``classFactory``.
"""


def classFactory(iface):  # noqa: N802 (nome exigido pelo QGIS)
    from .plugin import PluginPrefeituraBetim

    return PluginPrefeituraBetim(iface)
