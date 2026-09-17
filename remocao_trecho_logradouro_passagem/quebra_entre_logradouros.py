"""Fase 0: quebra pela própria camada de trechos (cruzamento entre logradouros).

A **camada de trechos** é fonte **obrigatória** de cruzamento na remoção de
trecho de passagem — sempre, sem parâmetro, além de qualquer **camada de
quebra** auxiliar. Roda antes de tudo: um trecho em escopo que cruza — com ou
sem nó compartilhado hoje, inclusive um X sem vértice em nenhum dos dois
lados — um trecho de **outro** ``COD_LOGRADOURO`` na vizinhança é dividido
ali; o outro ``COD_LOGRADOURO`` nunca é tocado, mesmo fora de escopo. Um
cruzamento entre trechos do **mesmo** ``COD_LOGRADOURO`` sem nó compartilhado
é atípico: não quebra, só gera aviso.

Reaproveita a primitiva de interseção interna de ``quebra.py`` — sempre linha
contra linha, já que a própria camada de trechos é sempre ``LineString`` (o
papel de borda de polígono fica só com as camadas de quebra auxiliares).

Todas as comparações leem a topologia **original** (o que o chamador passou),
nunca o resultado já cortado de outro trecho do próprio laço — assim o
resultado não depende da ordem em que os trechos em escopo são visitados.

Um pedaço criado aqui ainda não é uma feição de verdade: circula pelas
estruturas em memória por um id **temporário** (inteiro negativo, escolhido
por um contador interno que nunca colide com um id real de feição do QGIS,
que são sempre ≥ 0) até a aplicação final da edição, quando o chamador o
materializa junto dos demais registros novos.
"""

from qgis.core import QgsGeometry, QgsPointXY, QgsRectangle, QgsSpatialIndex

from .quebra import cortar, distancias_de_intersecao_interna


def _bbox_de(coords, tol):
    xs = [p.x() for p in coords]
    ys = [p.y() for p in coords]
    r = QgsRectangle(min(xs), min(ys), max(xs), max(ys))
    r.grow(tol)
    return r


def _indice_espacial(ids, coords_por_id, tol):
    idx = QgsSpatialIndex()
    for fid in ids:
        idx.addFeature(fid, _bbox_de(coords_por_id[fid], tol))
    return idx


def quebrar_cruzamentos_entre_logradouros(
    ids_escopo, coords_por_id, geom_por_id, cod_por_id, tol
):
    """Quebra cada trecho de ``ids_escopo`` onde cruza um trecho de **outro**
    ``COD_LOGRADOURO`` dentro de ``coords_por_id`` (a vizinhança já carregada
    em memória — inclui trechos fora de escopo, só como candidatos de
    cruzamento; nunca modificados).

    ``coords_por_id``/``geom_por_id``/``cod_por_id`` — dicionários por id de
    trecho, cobrindo toda a vizinhança (``ids_escopo`` é um subconjunto).

    Devolve ``(coords_por_id, geom_por_id, cod_por_id, novos, origem_real,
    pontos_de_corte, avisos)``:

    - ``coords_por_id``/``geom_por_id``/``cod_por_id`` — cópias atualizadas:
      um id original dividido passa a ter só o primeiro pedaço; cada pedaço
      seguinte entra com um id temporário novo (nunca um id real);
    - ``novos`` — lista de ``(id_temporario, fid_origem, [QgsPointXY, ...])``,
      **na ordem em que os ids temporários foram criados** — quem resolve a
      chave primária em lote (``resolver_chaves``) zipa essa ordem direto com
      os valores devolvidos, sem precisar adivinhar a ordem de criação;
    - ``origem_real`` — ``{id_temporario: id_original}``, para copiar
      atributos e resolver a chave primária;
    - ``pontos_de_corte`` — ``QgsPointXY`` de cada cruzamento dividido, para o
      chamador marcar como cruzamento no índice de nós compartilhado;
    - ``avisos`` — textos para o log (cruzamento atípico entre trechos do
      mesmo ``COD_LOGRADOURO`` sem nó compartilhado; nada é dividido nesse
      caso).
    """
    ids_escopo = set(ids_escopo)
    idx = _indice_espacial(coords_por_id.keys(), coords_por_id, tol)

    coords_por_id_orig = coords_por_id
    geom_por_id_orig = geom_por_id

    coords_novo = dict(coords_por_id)
    geom_novo = dict(geom_por_id)
    cod_novo = dict(cod_por_id)

    novos = []
    origem_real = {}
    pontos_de_corte = []
    avisos = []
    avisados = set()
    proximo_temp_id = -1

    for fid in sorted(ids_escopo):
        coords = coords_por_id_orig[fid]
        cod = cod_por_id[fid]
        linha = QgsGeometry.fromPolylineXY(coords)
        bbox = _bbox_de(coords, tol)

        geoms_outro_cod = []
        for cand in idx.intersects(bbox):
            if cand == fid:
                continue
            cand_cod = cod_por_id[cand]
            cand_geom = geom_por_id_orig[cand]
            if cand_cod == cod:
                if distancias_de_intersecao_interna(linha, [cand_geom], tol):
                    par = frozenset((fid, cand))
                    if par not in avisados:
                        avisados.add(par)
                        avisos.append(
                            "trechos {0} e {1} (mesmo COD_LOGRADOURO {2}) se "
                            "cruzam sem nó compartilhado; atípico, não "
                            "quebrado.".format(fid, cand, cod)
                        )
                continue
            geoms_outro_cod.append(cand_geom)

        if not geoms_outro_cod:
            continue
        distancias = distancias_de_intersecao_interna(linha, geoms_outro_cod, tol)
        if not distancias:
            continue

        pedacos = cortar(coords, distancias, tol)
        if len(pedacos) <= 1:
            continue

        coords_novo[fid] = pedacos[0]
        geom_novo[fid] = QgsGeometry.fromPolylineXY(pedacos[0])
        for pedaco in pedacos[1:]:
            pontos_de_corte.append(pedaco[0])
            temp_id = proximo_temp_id
            proximo_temp_id -= 1
            coords_novo[temp_id] = pedaco
            geom_novo[temp_id] = QgsGeometry.fromPolylineXY(pedaco)
            cod_novo[temp_id] = cod
            origem_real[temp_id] = fid
            novos.append((temp_id, fid, pedaco))

    return coords_novo, geom_novo, cod_novo, novos, origem_real, pontos_de_corte, avisos
