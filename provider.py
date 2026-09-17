"""Provider do Processing da Prefeitura de Betim.

Agrupa os algoritmos de geoprocessamento da PBH no Toolbox. Cada algoritmo
declara seu próprio grupo por escopo (Trecho logradouro, Logradouro, Lotes, ...).
"""

from qgis.core import QgsProcessingProvider

from .numeracao_trecho_logradouro.algoritmo import NumeracaoPorLogradouroAlgorithm
from .remocao_trecho_logradouro_passagem.algoritmo import (
    RemoverTrechosPassagemAlgorithm,
)


class ProviderPrefeituraBetim(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(NumeracaoPorLogradouroAlgorithm())
        self.addAlgorithm(RemoverTrechosPassagemAlgorithm())

    def id(self):
        return "prefeituradebetim"

    def name(self):
        return "Prefeitura de Betim"

    def longName(self):
        return "Prefeitura de Betim"
