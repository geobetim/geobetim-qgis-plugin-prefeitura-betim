"""Índice de nós dos trechos, por tolerância de encaixe.

Cada ponta de trecho vira (ou reaproveita) um nó, se cair dentro da tolerância
de encaixe de um nó já existente. A busca do nó existente usa um
``QgsSpatialIndex`` para não cair em O(n²) numa camada com milhares de trechos.

O índice é neutro em relação a `COD_LOGRADOURO`: guarda, por nó, todas as pontas
de trecho que caem nele (com o código de cada uma). Cada consumidor decide o que
é "grau" no seu recorte — a numeração restringe ao logradouro alvo, a remoção de
trechos de passagem restringe ao código sendo processado — e usa
``codigos_no_no`` para saber se outro logradouro também toca o nó.
"""

from qgis.core import QgsRectangle, QgsSpatialIndex


class IndiceDeNos:
    def __init__(self, tolerancia_encaixe):
        self._tol = float(tolerancia_encaixe)
        self.nos = []  # list[QgsPointXY]
        self._idx = QgsSpatialIndex()
        self._trechos_por_no = {}  # int -> list[(id_trecho, cod)]
        self._extremos = {}  # id_trecho -> (no_inicio, no_fim)

    def indexar(self, id_trecho, cod, ponta_inicio, ponta_fim):
        """Registra um trecho pelos seus dois extremos. Devolve ``(no_ini, no_fim)``."""
        a = self.achar_ou_criar_no(ponta_inicio)
        b = self.achar_ou_criar_no(ponta_fim)
        self._extremos[id_trecho] = (a, b)
        self._trechos_por_no[a].append((id_trecho, cod))
        self._trechos_por_no[b].append((id_trecho, cod))
        return a, b

    def achar_ou_criar_no(self, p):
        if self.nos:
            vizinhos = self._idx.nearestNeighbor(p, 1)
            if vizinhos and self.nos[vizinhos[0]].distance(p) <= self._tol:
                return vizinhos[0]
        i = len(self.nos)
        self.nos.append(p)
        self._trechos_por_no[i] = []
        self._idx.addFeature(i, QgsRectangle(p.x(), p.y(), p.x(), p.y()))
        return i

    def extremos_do_trecho(self, id_trecho):
        return self._extremos[id_trecho]

    def trechos_no_no(self, no):
        """Lista de ``(id_trecho, cod)`` de todas as pontas que caem no nó."""
        return self._trechos_por_no[no]

    def grau(self, no):
        """Grau bruto: quantas pontas de trecho (de qualquer código) caem no nó."""
        return len(self._trechos_por_no[no])

    def codigos_no_no(self, no):
        return {cod for _, cod in self._trechos_por_no[no]}

    def mesmo_ponto(self, a, b):
        return a.distance(b) <= self._tol
