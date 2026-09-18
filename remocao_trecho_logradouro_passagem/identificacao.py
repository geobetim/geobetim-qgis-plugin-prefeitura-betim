"""Identificação dos segmentos de passagem de um logradouro.

Um **nó de passagem** reúne exatamente duas pontas de trecho do mesmo
``COD_LOGRADOURO``, de dois trechos distintos, nenhuma ponta de outro
``COD_LOGRADOURO`` (nem bifurcação), e nenhuma feição de camada de quebra
encostada. Um **segmento de passagem** é uma sequência maximal de trechos do
mesmo código ligados só por nós de passagem, com **2 ou mais** trechos — é o que
a operação colapsa num trecho só. O recorte é o grafo restrito ao código.

Um **trecho degenerado** (as duas pontas caem no mesmo nó, dentro da
tolerância de encaixe — ver ADR-0008/ADR-0009) nunca conta como ponta ao
decidir se um nó é nó de passagem — só os trechos reais contam, e ele nunca
entra na lista ordenada de um segmento nem em ``colapsar``. Em vez disso,
``trecho_degenerado_fundivel`` acha o maior trecho real do mesmo código que
toca o nó dele — mesmo fora de um nó de passagem (ADR-0009: o trecho
degenerado sempre funde com o maior vizinho real, mesmo num cruzamento,
exceto se isolado ou bloqueado por camada de quebra). A fusão nunca precisa
de geometria nova: o nó do trecho degenerado só existe porque uma ponta do
vizinho já cai dentro da tolerância de encaixe *desse mesmo nó* — o vizinho
já tem, por construção, um vértice ali. Quem chama só usa o vizinho
devolvido para decidir se apaga o trecho degenerado; nenhuma geometria é
alterada.
"""

from .absorcao import maior_por_comprimento


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
    ``trecho_degenerado_fundivel`` cobre a fusão deles. ``degenerados``
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


def trecho_degenerado_fundivel(indice, id_degenerado, ids_cod, nos_bloqueados, geom_por_id, valor_pk_por_id=None):
    """Maior trecho real (mesmo critério de desempate do **trecho
    absorvedor**: comprimento, empate pela chave primária ou pelo menor id)
    do mesmo ``COD_LOGRADOURO`` que toca o nó de ``id_degenerado`` — ou
    ``None`` se não houver nenhum (isolado) ou se o nó estiver bloqueado por
    camada de quebra (sinal explícito do operador, que continua impedindo a
    fusão ali — ver ADR-0009). ``ids_cod`` já deve ser um ``set`` — quem
    chama isto por vários trechos degenerados do mesmo código evita
    reconverter a cada chamada.
    """
    no = indice.extremos_do_trecho(id_degenerado)[0]
    if no in nos_bloqueados:
        return None
    vizinhos = [
        tid
        for tid, _ in indice.trechos_no_no(no)
        if tid in ids_cod and tid != id_degenerado and not indice.eh_degenerado(tid)
    ]
    if not vizinhos:
        return None
    return maior_por_comprimento(vizinhos, geom_por_id, valor_pk_por_id)
