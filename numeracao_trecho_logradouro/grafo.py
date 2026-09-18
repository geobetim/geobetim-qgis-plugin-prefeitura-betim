"""Grafo de nós dos trechos de um logradouro.

O índice de nós (``shared.topologia.IndiceDeNos``) é montado no construtor sobre
**todos** os trechos da vizinhança e compartilhado entre os logradouros de uma
execução. As arestas usadas para percorrer (``adjacencia`` / ``graus`` /
``extremos_do_trecho``) e os cruzamentos são recalculados a cada chamada de
``definir_alvo``, para o único ``COD_LOGRADOURO`` sendo sequenciado no momento —
assim um logradouro nunca "vaza" para dentro do percurso de outro, mesmo
compartilhando o mesmo índice de nós.
"""

from qgis.core import QgsPointXY

from ..shared.topologia import IndiceDeNos
from .erros import NumeracaoError


class TrechoParseado:
    __slots__ = ("id", "cod", "geom", "coords")

    def __init__(self, id_trecho, cod, geom, coords):
        self.id = id_trecho
        self.cod = cod
        self.geom = geom
        self.coords = coords  # list[QgsPointXY], do início ao fim

    @property
    def inicio(self):
        return self.coords[0]

    @property
    def fim(self):
        return self.coords[-1]


class Incidencia:
    __slots__ = ("id_trecho", "outro_no")

    def __init__(self, id_trecho, outro_no):
        self.id_trecho = id_trecho
        self.outro_no = outro_no


def parse_geometria(id_trecho, cod, geom):
    """
    Extrai os vértices de um ``QgsGeometry`` (achata multipartes, mantém a
    ordem). Primeiro vértice = início, último = fim.
    """
    coords = [QgsPointXY(v) for v in geom.vertices()]
    if len(coords) < 2:
        raise NumeracaoError("Trecho {0} tem menos de 2 vértices.".format(id_trecho))
    return TrechoParseado(id_trecho, cod, geom, coords)


class GrafoLogradouro:
    def __init__(self, todos, tolerancia_encaixe):
        """``todos``: iterável de ``TrechoParseado`` de qualquer COD_LOGRADOURO."""
        self._tol = float(tolerancia_encaixe)
        self._indice = IndiceDeNos(self._tol)
        for t in todos:
            self._indice.indexar(t.id, t.cod, t.inicio, t.fim)
        self.nos = self._indice.nos  # list[QgsPointXY]

        # Preenchidos por definir_alvo().
        self.graus = None
        self.adjacencia = None
        self.extremos_do_trecho = None
        self.cruzamentos = None
        self.degenerados = None

    def definir_alvo(self, alvo):
        """
        Recalcula arestas, grau e cruzamentos para os trechos de ``alvo`` —
        todos do mesmo COD_LOGRADOURO. Um nó é cruzamento se tiver grau >= 3
        dentro deste alvo (bifurcação) ou se algum trecho de outro
        COD_LOGRADOURO também tocar esse nó.

        Um trecho degenerado (as duas pontas caem no mesmo nó, dentro da
        tolerância de encaixe) não conta para grau/adjacência/cruzamento —
        ele nunca representa deslocamento real, então nunca deve ser
        candidato de percurso nem inflar a contagem de um nó (ver
        ADR-0008). Seu mapeamento trecho->nó continua em
        ``extremos_do_trecho``, para a atribuição de número sequencial achar
        o nó compartilhado com os vizinhos.
        """
        self.graus = [0] * len(self.nos)
        self.adjacencia = {i: [] for i in range(len(self.nos))}
        self.extremos_do_trecho = {}
        self.degenerados = set()

        for t in alvo:
            a, b = self._indice.extremos_do_trecho(t.id)
            self.extremos_do_trecho[t.id] = (a, b)
            if self._indice.eh_degenerado(t.id):
                self.degenerados.add(t.id)
                continue
            self.adjacencia[a].append(Incidencia(t.id, b))
            self.graus[a] += 1
            self.adjacencia[b].append(Incidencia(t.id, a))
            self.graus[b] += 1

        self.cruzamentos = set()
        for extremos in self.extremos_do_trecho.values():
            for no in extremos:
                if self.graus[no] >= 3 or len(self._indice.codigos_no_no(no)) > 1:
                    self.cruzamentos.add(no)

    def outro_no(self, id_trecho, no):
        e = self.extremos_do_trecho[id_trecho]
        return e[1] if e[0] == no else e[0]

    def no_compartilhado(self, a, b):
        """Nó que dois trechos compartilham, ou -1 se não compartilham nenhum."""
        ea = self.extremos_do_trecho.get(a)
        eb = self.extremos_do_trecho.get(b)
        if ea is None or eb is None:
            return -1
        if eb[0] == ea[0] or eb[0] == ea[1]:
            return eb[0]
        if eb[1] == ea[0] or eb[1] == ea[1]:
            return eb[1]
        return -1

    def mesmo_ponto(self, a, b):
        return a.distance(b) <= self._tol
