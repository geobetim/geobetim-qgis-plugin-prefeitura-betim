"""Identificação dos segmentos de passagem de um logradouro.

Um **nó de passagem** reúne exatamente duas pontas de trecho do mesmo
``COD_LOGRADOURO``, de dois trechos distintos, nenhuma ponta de outro
``COD_LOGRADOURO`` (nem bifurcação), e nenhuma feição de camada de quebra
encostada. Um **segmento de passagem** é uma sequência maximal de trechos do
mesmo código ligados só por nós de passagem, com **2 ou mais** trechos — é o que
a operação colapsa num trecho só. O recorte é o grafo restrito ao código.
"""


def _no_de_passagem(indice, no, cod, ids_cod, nos_bloqueados):
    if no in nos_bloqueados:
        return False
    pontas_do_cod = [tid for tid, _ in indice.trechos_no_no(no) if tid in ids_cod]
    if len(pontas_do_cod) != 2 or len(set(pontas_do_cod)) != 2:
        return False
    return not (indice.codigos_no_no(no) - {cod})


def _ordenar(comp, adjacencia):
    """Ordena o componente como caminho (ou ciclo, começando no menor id)."""
    graus = {t: len(adjacencia[t] & comp) for t in comp}
    pontas = [t for t in sorted(comp) if graus[t] == 1]
    inicio = pontas[0] if pontas else min(comp)
    ordem = [inicio]
    anterior = None
    atual = inicio
    while len(ordem) < len(comp):
        seguintes = [
            t
            for t in sorted(adjacencia[atual] & comp)
            if t != anterior and t not in ordem
        ]
        if not seguintes:
            break
        anterior, atual = atual, seguintes[0]
        ordem.append(atual)
    return ordem


def segmentos_de_passagem(indice, ids_cod, cod, nos_bloqueados):
    """Lista de segmentos de passagem (≥ 2 trechos), cada um ordenado como caminho.

    ``nos_bloqueados`` — índices de nó tocados por camada de quebra (viram
    cruzamento).
    """
    ids_cod = set(ids_cod)
    adjacencia = {t: set() for t in ids_cod}
    for t in ids_cod:
        a, b = indice.extremos_do_trecho(t)
        if a == b:
            continue
        for no in (a, b):
            if _no_de_passagem(indice, no, cod, ids_cod, nos_bloqueados):
                for outro, _ in indice.trechos_no_no(no):
                    if outro in ids_cod and outro != t:
                        adjacencia[t].add(outro)

    visto = set()
    segmentos = []
    for start in sorted(ids_cod):
        if start in visto:
            continue
        comp = {start}
        visto.add(start)
        pilha = [start]
        while pilha:
            x = pilha.pop()
            for y in adjacencia[x]:
                if y not in comp:
                    comp.add(y)
                    visto.add(y)
                    pilha.append(y)
        if len(comp) >= 2:
            segmentos.append(_ordenar(comp, adjacencia))
    return segmentos
