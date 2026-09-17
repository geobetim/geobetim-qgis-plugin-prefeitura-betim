"""Numeração dos trechos de um logradouro na ordem espacial.

- ``algoritmo``: o ``QgsProcessingAlgorithm`` "Numeração de trechologradouro por
  logradouro".
- ``grafo``: monta-se sobre ``shared.topologia`` e marca os cruzamentos do
  logradouro alvo.
- ``sequenciador``: produz a ordem espacial dos trechos de um logradouro
  (percurso em profundidade a partir de uma extremidade, encadeando trechos
  desconectados pela proximidade).
- ``atribuidor``: numera os trechos por segmento — começa em 1, avança a cada
  cruzamento, repete entre trechos contíguos do mesmo segmento.
"""

from .atribuidor import atribuir
from .erros import NumeracaoError
from .grafo import GrafoLogradouro, TrechoParseado, parse_geometria
from .sequenciador import SequenciadorAutomatico

__all__ = [
    "atribuir",
    "NumeracaoError",
    "GrafoLogradouro",
    "TrechoParseado",
    "parse_geometria",
    "SequenciadorAutomatico",
]
