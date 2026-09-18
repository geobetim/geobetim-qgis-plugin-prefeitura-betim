"""Colapso de um segmento de passagem num trecho só.

Cada **segmento de passagem** (lista ordenada de 2+ ids de trecho) colapsa: o
**trecho absorvedor** — o maior por comprimento, empate pelo **menor** valor da
chave primária configurada (ou, sem ela, pelo menor id da feição) — é o único
registro que sobrevive; sua geometria é estendida para passar por **todos** os
vértices dos demais trechos do segmento, na ordem; os outros são apagados. Um
segmento fechado (o logradouro é um anel de nós de passagem) vira um trecho
fechado que **começa e termina no nó de fechamento** — o nó compartilhado pela
primeira e pela última ponta do segmento, em geral um cruzamento (um "balão"
preso a uma via) — para quem encostava nesse nó continuar encostando numa
ponta do trecho, não no meio dele. A emenda do anel orienta o primeiro trecho
pelo nó de fechamento e cada seguinte pela ponta comum, então não depende da
orientação em que a geometria do absorvedor está no banco.
"""


def _mesmo(a, b, tol):
    return a.distance(b) <= tol


def maior_por_comprimento(ids, geom_por_id, valor_pk_por_id=None):
    """Maior por comprimento 2D; empate pelo menor valor de ``valor_pk_por_id``
    quando disponível, senão pelo menor id da feição."""

    def chave_desempate(t):
        if valor_pk_por_id is not None:
            v = valor_pk_por_id.get(t)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
        return float(t)

    return max(ids, key=lambda t: (geom_por_id[t].length(), -chave_desempate(t)))


def _limpar_consecutivos(coords, tol):
    saida = [coords[0]]
    for p in coords[1:]:
        if not _mesmo(saida[-1], p, tol):
            saida.append(p)
    return saida


def _estender(base, r, tol):
    """Liga os vértices de ``r`` a ``base`` pela ponta comum.

    Devolve a nova lista de coordenadas, ou ``None`` se ``r`` não compartilha
    exatamente uma ponta com ``base`` (inclui o caso de laço: as duas pontas).

    Quando ``r`` é ele mesmo curtíssimo (um trecho degenerado — ver
    ADR-0009/0010), as duas pontas de ``r`` podem cair dentro da tolerância
    da MESMA ponta de ``base`` ao mesmo tempo — nesse caso a ponta mais
    próxima é a duplicata (descartada) e a mais distante é o vértice novo
    que de fato estende ``base``. Para um ``r`` de comprimento normal isso
    nunca é ambíguo (só uma das pontas cai perto), então o resultado não
    muda em nenhum colapso comum.

    Quando o novo vértice acrescido também cai dentro da tolerância da
    ponta antiga de ``base`` (mesmo motivo: ``r`` curtíssimo), a antiga
    ponta de ``base`` é descartada em favor dele — senão ``_limpar_
    consecutivos`` manteria a ponta antiga (a primeira da dupla) e
    descartaria justo o vértice novo que a extensão deveria acrescentar.
    """
    p0, pn = base[0], base[-1]
    r0, rm = r[0], r[-1]

    toca_p0 = _mesmo(p0, r0, tol) or _mesmo(p0, rm, tol)
    toca_pn = _mesmo(pn, r0, tol) or _mesmo(pn, rm, tol)
    if toca_p0 and toca_pn:
        return None

    if toca_pn:
        r0_bate = _mesmo(pn, r0, tol)
        rm_bate = _mesmo(pn, rm, tol)
        if r0_bate and (not rm_bate or pn.distance(r0) <= pn.distance(rm)):
            novo = r[1:]
        else:
            novo = list(reversed(r))[1:]
        if novo and _mesmo(pn, novo[0], tol):
            return base[:-1] + novo
        return base + novo

    if toca_p0:
        r0_bate = _mesmo(p0, r0, tol)
        rm_bate = _mesmo(p0, rm, tol)
        if rm_bate and (not r0_bate or p0.distance(rm) <= p0.distance(r0)):
            return r[:-1] + base
        return list(reversed(r))[:-1] + base

    return None


def _encadear(ordem, coords_por_id, tol, ponto_inicio):
    """Concatena os vértices dos trechos de ``ordem`` numa polilinha única que
    **começa** em ``ponto_inicio``: o primeiro trecho é orientado por esse ponto
    (invertido se for a ponta final dele) e cada seguinte pela ponta comum com o
    anterior. Serve para o segmento fechado, com ``ponto_inicio`` = nó de
    fechamento. Devolve ``(incorporados, coords)`` ou ``(set(), None)``.
    """
    base = list(coords_por_id[ordem[0]])
    if len(base) < 2:
        return set(), None
    if _mesmo(base[-1], ponto_inicio, tol) and not _mesmo(base[0], ponto_inicio, tol):
        base.reverse()
    elif not _mesmo(base[0], ponto_inicio, tol):
        return set(), None
    incorporados = {ordem[0]}
    for tid in ordem[1:]:
        r = coords_por_id[tid]
        if len(r) < 2:
            return set(), None
        if _mesmo(base[-1], r[0], tol):
            base = base + r[1:]
        elif _mesmo(base[-1], r[-1], tol):
            base = base + list(reversed(r))[1:]
        else:
            return set(), None
        incorporados.add(tid)
    return incorporados, _limpar_consecutivos(base, tol)


def _incorporar_lado(base, trechos, coords_por_id, tol, avisos):
    incorporados = set()
    for tid in trechos:
        r = coords_por_id[tid]
        if len(r) < 2:
            avisos.append(
                "trecho {0} tem menos de 2 vértices; não removido.".format(tid)
            )
            continue
        novo = _estender(base, r, tol)
        if novo is None:
            avisos.append(
                "trecho {0} não encadeia no segmento; não removido.".format(tid)
            )
            continue
        base = _limpar_consecutivos(novo, tol)
        incorporados.add(tid)
    return incorporados, base


def colapsar(segmentos, indice, coords_por_id, geom_por_id, tol, valor_pk_por_id=None):
    """Colapsa cada segmento. Devolve ``(geom_nova, apagar, avisos)``:

    - ``geom_nova`` — ``{id_absorvedor: [QgsPointXY, ...]}``;
    - ``apagar`` — ids de trecho a apagar (nunca inclui um absorvedor);
    - ``avisos`` — trechos pulados.

    ``valor_pk_por_id`` — ``{id_trecho: valor}`` do atributo configurado como
    chave primária, usado para desempatar o absorvedor (menor valor). Opcional;
    sem ele, o desempate cai no id da feição.
    """
    geom_nova = {}
    apagar = set()
    avisos = []

    for seg in segmentos:
        if len(seg) < 2:
            continue
        absorvedor = maior_por_comprimento(seg, geom_por_id, valor_pk_por_id)

        pontas_ini = set(indice.extremos_do_trecho(seg[0]))
        pontas_fim = set(indice.extremos_do_trecho(seg[-1]))
        nos_fechamento = pontas_ini & pontas_fim
        eh_ciclo = len(seg) >= 3 and bool(nos_fechamento)

        if eh_ciclo:
            # Anel: emenda na ordem do segmento, começando (e terminando) no nó
            # de fechamento. O absorvedor só é o registro que sobrevive — não
            # precisa ser o primeiro da emenda.
            no_fechamento = min(nos_fechamento)
            incorporados, base = _encadear(
                seg, coords_por_id, tol, indice.nos[no_fechamento]
            )
            if base is None:
                avisos.append(
                    "segmento fechado {0} não encadeia; não colapsado.".format(
                        sorted(seg)
                    )
                )
                continue
            geom_nova[absorvedor] = base
            apagar |= incorporados - {absorvedor}
            continue

        i = seg.index(absorvedor)
        esquerda = list(reversed(seg[:i]))
        direita = seg[i + 1 :]
        base = list(coords_por_id[absorvedor])
        inc_e, base = _incorporar_lado(base, esquerda, coords_por_id, tol, avisos)
        inc_d, base = _incorporar_lado(base, direita, coords_por_id, tol, avisos)
        incorporados = inc_e | inc_d
        if incorporados:
            geom_nova[absorvedor] = _limpar_consecutivos(base, tol)
            apagar |= incorporados

    apagar -= set(geom_nova.keys())
    return geom_nova, apagar, avisos
