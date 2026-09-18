"""Identificação dos segmentos de passagem de um logradouro.

Um **nó de passagem** reúne exatamente duas pontas de trecho do mesmo
``COD_LOGRADOURO``, de dois trechos distintos, nenhuma ponta de outro
``COD_LOGRADOURO`` (nem bifurcação), e nenhuma feição de camada de quebra
encostada. Um **segmento de passagem** é uma sequência maximal de trechos do
mesmo código ligados só por nós de passagem, com **2 ou mais** trechos — é o que
a operação colapsa num trecho só. O recorte é o grafo restrito ao código.

Um **trecho degenerado** (as duas pontas caem no mesmo nó, dentro da
tolerância de encaixe — ver ADR-0008) nunca conta como ponta ao decidir se um
nó é nó de passagem — só os trechos reais contam, e ele nunca entra na lista
ordenada de um segmento (``colapsar`` não muda: inserir um trecho cujas duas
pontas coincidem no meio de um segmento de 2 trechos reais confundiria a
heurística de anel fechado, que olha só se o primeiro e o último elemento
compartilham nó). Em vez disso, ``trechos_degenerados_absorviveis`` mapeia
cada trecho degenerado aos seus vizinhos reais; quem chama ``colapsar``
decide, depois, se esses vizinhos de fato colapsaram — e se sim, apaga o
trecho degenerado junto, sem lhe dar geometria própria.
"""


def trechos_degenerados(indice, ids_cod):
    return {t for t in ids_cod if indice.eh_degenerado(t)}


def _no_de_passagem(indice, no, cod, ids_cod, nos_bloqueados, degenerados):
    if no in nos_bloqueados:
        return False
    pontas_do_cod = [
        tid
        for tid, _ in indice.trechos_no_no(no)
        if tid in ids_cod and tid not in degenerados
    ]
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


def segmentos_de_passagem(indice, ids_cod, cod, nos_bloqueados, degenerados=None):
    """Lista de segmentos de passagem (≥ 2 trechos), cada um ordenado como caminho.

    ``nos_bloqueados`` — índices de nó tocados por camada de quebra (viram
    cruzamento). Trechos degenerados (ver ADR-0008) nunca entram nem na
    contagem de grau, nem na lista ordenada — só os reais formam segmento;
    ``trechos_degenerados_absorviveis`` cobre a absorção deles. ``degenerados``
    é opcional — quem já os calculou (ex.: para o aviso de feedback) evita
    recalcular sobre a mesma coleção de ids.
    """
    ids_cod = set(ids_cod)
    degenerados = trechos_degenerados(indice, ids_cod) if degenerados is None else degenerados
    reais = ids_cod - degenerados
    adjacencia = {t: set() for t in reais}
    for t in reais:
        a, b = indice.extremos_do_trecho(t)
        for no in (a, b):
            if _no_de_passagem(indice, no, cod, ids_cod, nos_bloqueados, degenerados):
                for outro, _ in indice.trechos_no_no(no):
                    if outro in reais and outro != t:
                        adjacencia[t].add(outro)

    visto = set()
    segmentos = []
    for start in sorted(reais):
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


def trechos_degenerados_absorviveis(indice, ids_cod, cod, nos_bloqueados, degenerados=None):
    """``{trecho_degenerado: (vizinho_real_1, vizinho_real_2)}`` — só para os
    trechos degenerados cujo nó é nó de passagem real entre dois trechos do
    mesmo ``COD_LOGRADOURO``. Quem chama ``colapsar`` sobre os segmentos de
    ``segmentos_de_passagem`` usa isto depois: se um dos vizinhos de um
    trecho degenerado aparecer no resultado do colapso (absorvido ou
    apagado), o trecho degenerado apaga junto, sem geometria própria — nunca
    é ele quem decide a geometria do trecho absorvedor. ``degenerados`` é
    opcional, mesmo motivo de ``segmentos_de_passagem``.
    """
    ids_cod = set(ids_cod)
    degenerados = trechos_degenerados(indice, ids_cod) if degenerados is None else degenerados
    resultado = {}
    for d in degenerados:
        no = indice.extremos_do_trecho(d)[0]
        if not _no_de_passagem(indice, no, cod, ids_cod, nos_bloqueados, degenerados):
            continue
        vizinhos = tuple(
            tid
            for tid, _ in indice.trechos_no_no(no)
            if tid in ids_cod and tid != d
        )
        resultado[d] = vizinhos
    return resultado
