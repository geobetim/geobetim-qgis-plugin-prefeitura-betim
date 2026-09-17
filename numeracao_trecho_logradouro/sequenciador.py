"""Ordem espacial dos trechos de um logradouro.

 1. trecho inicial — entre as extremidades do logradouro, ordenadas pela
    distância ao canto inferior esquerdo do MBR do logradouro inteiro (empate
    pelo menor id), tenta cada uma nessa ordem e fica com a primeira que
    consegue numerar TODOS os trechos. Importa com componentes desconexos: a
    extremidade mais perto do canto pode estar colada a um vão. Anel fechado
    (sem extremidade) usa uma única tentativa: vértice mais próximo do canto;
 2. percurso em profundidade — na bifurcação segue a continuação mais reta e
    depois volta ao nó de bifurcação pendente mais recente (LIFO);
 3. componentes disjuntos são alcançados encadeando pela ponta mais próxima do
    último vértice numerado, respeitando a tolerância de gap.
"""

from qgis.core import QgsPointXY, QgsVector

from .erros import NumeracaoError

_EPS = 1e-9


class CandidatoInicio:
    __slots__ = ("id", "no_origem", "distancia_ao_canto")

    def __init__(self, id_trecho, no_origem, distancia_ao_canto):
        self.id = id_trecho
        self.no_origem = no_origem
        self.distancia_ao_canto = distancia_ao_canto


class SequenciadorAutomatico:
    def __init__(self, cod, alvo, grafo, tolerancia_gap):
        self._cod = cod
        self._alvo = list(alvo)
        self._grafo = grafo
        self._tol_gap = float(tolerancia_gap)
        self._por_id = {t.id: t for t in self._alvo}

        # Estado de UMA tentativa — reiniciado a cada _tentar().
        self._ordem = []
        self._usados = set()
        self._junction_stack = []
        self._direcao_na_chegada = {}
        self._no_atual = -1
        self._direcao_chegada = QgsVector(1.0, 0.0)

    def run(self):
        candidatos = self._candidatos_de_partida()
        ultima_falha = None
        for c in candidatos:
            try:
                return self._tentar(c.id, c.no_origem)
            except NumeracaoError as ex:
                ultima_falha = ex
        if ultima_falha is not None:
            raise ultima_falha
        raise NumeracaoError(
            "Não há trecho inicial elegível para o COD_LOGRADOURO {0}.".format(self._cod)
        )

    def _tentar(self, inicio_id, no_origem):
        self._ordem = []
        self._usados = set()
        self._junction_stack = []
        self._direcao_na_chegada = {}

        t0 = self._por_id[inicio_id]
        self._ordem.append(inicio_id)
        self._usados.add(inicio_id)
        self._direcao_chegada = self._direcao_de_saida(t0, no_origem)
        self._no_atual = self._grafo.outro_no(inicio_id, no_origem)
        self._registrar_junction(self._no_atual)

        while len(self._usados) < len(self._alvo):
            candidatos = self._candidatos(self._no_atual)

            if not candidatos:
                alvo_j = self._desempilhar_ate_junction_com_ramo()
                if alvo_j < 0:
                    if not self._continuar_disjunto():
                        break
                    continue
                self._no_atual = alvo_j
                d = self._direcao_na_chegada.get(alvo_j)
                if d is not None:
                    self._direcao_chegada = d
                continue

            if len(candidatos) == 1:
                self._percorrer(candidatos[0])
                continue

            # Bifurcação: continuação mais reta (maior produto escalar entre a
            # direção de deslocamento e a direção de entrada do candidato).
            # QgsVector * QgsVector devolve o produto escalar (float).
            escolhido = sorted(
                candidatos,
                key=lambda inc: (
                    -(self._direcao_chegada * self._direcao_de_entrada(inc)),
                    inc.id_trecho,
                ),
            )[0]

            if self._no_atual not in self._junction_stack:
                self._junction_stack.append(self._no_atual)
                self._direcao_na_chegada[self._no_atual] = self._direcao_chegada
            self._percorrer(escolhido)

        if len(self._ordem) != len(self._alvo):
            raise NumeracaoError(
                "Nem todos os trechos do COD_LOGRADOURO {0} puderam ser numerados "
                "a partir do trecho inicial {1}.".format(self._cod, inicio_id)
            )
        return list(self._ordem)

    # ---- trecho inicial --------------------------------------------------

    def _candidatos_de_partida(self):
        min_x = min_y = None
        for t in self._alvo:
            for c in t.coords:
                if min_x is None or c.x() < min_x:
                    min_x = c.x()
                if min_y is None or c.y() < min_y:
                    min_y = c.y()
        canto = QgsPointXY(min_x, min_y)

        extremidades = [
            t
            for t in self._alvo
            if self._grafo.graus[self._grafo.extremos_do_trecho[t.id][0]] == 1
            or self._grafo.graus[self._grafo.extremos_do_trecho[t.id][1]] == 1
        ]

        if extremidades:
            cands = []
            for t in extremidades:
                e = self._grafo.extremos_do_trecho[t.id]
                no_g1 = e[0] if self._grafo.graus[e[0]] == 1 else e[1]
                cands.append(
                    CandidatoInicio(t.id, no_g1, self._grafo.nos[no_g1].distance(canto))
                )
            cands.sort(key=lambda c: (c.distancia_ao_canto, c.id))
            return cands

        # Anel fechado: nenhum trecho de grau 1. Uma única tentativa.
        best = None
        best_d = None
        for t in self._alvo:
            d = min(c.distance(canto) for c in t.coords)
            if self._melhor(d, t.id, best_d, best):
                best = t
                best_d = d
        if best is None:
            return []
        e = self._grafo.extremos_do_trecho[best.id]
        no_origem = (
            e[0] if best.inicio.distance(canto) <= best.fim.distance(canto) else e[1]
        )
        return [CandidatoInicio(best.id, no_origem, best_d)]

    @staticmethod
    def _melhor(d, id_trecho, best_d, best):
        if best is None:
            return True
        if d < best_d - _EPS:
            return True
        if abs(d - best_d) <= _EPS and id_trecho < best.id:
            return True
        return False

    # ---- percurso ------------------------------------------------------

    def _candidatos(self, no):
        return [
            inc
            for inc in self._grafo.adjacencia[no]
            if inc.id_trecho not in self._usados
        ]

    def _desempilhar_ate_junction_com_ramo(self):
        while self._junction_stack:
            topo = self._junction_stack[-1]
            if self._candidatos(topo):
                return topo
            self._junction_stack.pop()
        return -1

    def _percorrer(self, inc):
        t = self._por_id[inc.id_trecho]
        self._ordem.append(inc.id_trecho)
        self._usados.add(inc.id_trecho)
        self._direcao_chegada = self._direcao_de_saida(t, self._no_atual)
        self._no_atual = inc.outro_no
        self._registrar_junction(self._no_atual)

    def _registrar_junction(self, no):
        if len(self._candidatos(no)) >= 2 and no not in self._junction_stack:
            self._junction_stack.append(no)
            self._direcao_na_chegada[no] = self._direcao_chegada

    def _continuar_disjunto(self):
        if len(self._usados) >= len(self._alvo):
            return False

        ultimo = self._grafo.nos[self._no_atual]

        best = None
        melhor_ponta = None
        best_d = None
        for t in self._alvo:
            if t.id in self._usados:
                continue
            for ponta in (t.inicio, t.fim):
                d = ponta.distance(ultimo)
                if self._melhor(d, t.id, best_d, best):
                    best = t
                    melhor_ponta = ponta
                    best_d = d
        if best is None:
            return False

        if best_d > self._tol_gap:
            ultimo_id = self._ordem[-1]
            raise NumeracaoError(
                "Trecho disjunto do COD_LOGRADOURO {0}: {1:.2f} m entre o último "
                "trecho numerado (id {2}) e o mais próximo ainda não numerado "
                "(id {3}) — acima da tolerância de gap de {4} m.".format(
                    self._cod, best_d, ultimo_id, best.id, self._tol_gap
                )
            )

        e = self._grafo.extremos_do_trecho[best.id]
        no_entrada = e[0] if self._grafo.mesmo_ponto(best.inicio, melhor_ponta) else e[1]

        self._ordem.append(best.id)
        self._usados.add(best.id)
        self._direcao_chegada = self._direcao_de_saida(best, no_entrada)
        self._no_atual = self._grafo.outro_no(best.id, no_entrada)
        self._registrar_junction(self._no_atual)
        return True

    # ---- geometria ---------------------------------------------------

    def _direcao_de_saida(self, t, no_entrada):
        pelo_inicio = self._grafo.mesmo_ponto(t.inicio, self._grafo.nos[no_entrada])
        n = len(t.coords)
        if pelo_inicio:
            p1, p2 = t.coords[n - 2], t.coords[n - 1]
        else:
            p1, p2 = t.coords[1], t.coords[0]
        return _unit(p2.x() - p1.x(), p2.y() - p1.y())

    def _direcao_de_entrada(self, inc):
        t = self._por_id[inc.id_trecho]
        pelo_inicio = self._grafo.mesmo_ponto(t.inicio, self._grafo.nos[self._no_atual])
        n = len(t.coords)
        if pelo_inicio:
            p1, p2 = t.coords[0], t.coords[1]
        else:
            p1, p2 = t.coords[n - 1], t.coords[n - 2]
        return _unit(p2.x() - p1.x(), p2.y() - p1.y())


def _unit(dx, dy):
    v = QgsVector(dx, dy)
    if v.length() <= _EPS:
        return QgsVector(0.0, 0.0)
    return v.normalized()
