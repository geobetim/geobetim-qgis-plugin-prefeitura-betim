"""Camadas de quebra: nós que viram cruzamento e recorte de trechos.

- ``nos_tocados_por_quebra`` (fase 1): índices de nó em que uma feição de camada
  de quebra encosta — passam a ser cruzamento, então o segmento de passagem para
  ali.
- ``quebrar`` (fase 2): para cada trecho em escopo (colapsado ou não), se ele
  cruza uma feição de quebra num ponto **interno**, é dividido ali. Primitivas
  nativas do QGIS: ``QgsGeometry.intersection`` para os pontos, ``lineLocatePoint``
  para a distância ao longo da linha e ``QgsCurve.curveSubstring`` para os
  pedaços.

Uma feição de quebra **poligonal** conta pela sua **borda**, nunca pela área
cheia — um ponto no interior, longe de qualquer borda, não "encosta" nem
"cruza". ``_fronteira`` extrai essa borda (inclui buracos); feição de linha
passa direto.

``intersecao_interna``/``distancias_de_intersecao_interna``/``cortar`` são a
primitiva geométrica pura (linha × geometrias já prontas para comparar, sem
nenhuma leitura de camada) — reaproveitada pela quebra pela própria camada de
trechos (cruzamento entre logradouros), que compara contra trechos já
carregados em memória em vez de reler uma ``QgsVectorLayer``.
"""

from qgis.core import (
    QgsFeatureRequest,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
    QgsSpatialIndex,
    QgsWkbTypes,
)


def _fronteira(g):
    """Borda de uma feição poligonal, como linha; feições não-poligonais voltam
    inalteradas."""
    if QgsWkbTypes.geometryType(g.wkbType()) == QgsWkbTypes.PolygonGeometry:
        linha = g.convertToType(QgsWkbTypes.LineGeometry, False)
        if linha is not None and not linha.isEmpty():
            return linha
    return g


def nos_tocados_por_quebra(nos, camadas_quebra, tol):
    """Índices de ``nos`` (lista de ``QgsPointXY``) a ≤ ``tol`` da borda de
    alguma feição das camadas de quebra."""
    if not camadas_quebra:
        return set()

    idx = QgsSpatialIndex()
    geoms = {}
    seq = 0
    for camada in camadas_quebra:
        for f in camada.getFeatures():
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            seq += 1
            geoms[seq] = _fronteira(g)
            r = g.boundingBox()
            r.grow(tol)
            idx.addFeature(seq, r)

    bloqueados = set()
    for i, p in enumerate(nos):
        pg = QgsGeometry.fromPointXY(p)
        rect = QgsRectangle(p.x() - tol, p.y() - tol, p.x() + tol, p.y() + tol)
        for cand in idx.intersects(rect):
            if geoms[cand].distance(pg) <= tol:
                bloqueados.add(i)
                break
    return bloqueados


def _partes(geometria):
    """As partes (``QgsAbstractGeometry``) de ``geometria`` — uma lista com a
    própria geometria para uma feição simples, ou uma por elemento para uma
    multi-geometria (ex.: a borda de um polígono com buracos, cada anel uma
    parte independente)."""
    corpo = geometria.constGet()
    if geometria.isMultipart():
        return [corpo.geometryN(i) for i in range(corpo.numGeometries())]
    return [corpo]


def _pontas(geometria):
    """Pontos (``QgsGeometry`` de ponto) candidatos a "quase toque" de cada
    parte de ``geometria``: o primeiro e o último vértice para uma parte
    aberta (linha comum). Um anel fechado — a borda de um polígono via
    ``_fronteira``, cada anel (externo ou de um buraco) sempre fechado — não
    tem uma ponta real: o primeiro/último vértice de ``vertices()`` é só o
    ponto onde a conversão polígono→linha começou a percorrer aquele anel
    (com buracos, um vértice de emenda arbitrário por anel, sem relação com
    onde o anel de fato tangencia outra geometria). Nesse caso, todo vértice
    do anel volta como candidato — não só o de emenda. Vazia se a geometria
    não tiver vértice."""
    pontos = []
    for parte in _partes(geometria):
        vertices = list(parte.vertices())
        if not vertices:
            continue
        primeiro, ultimo = QgsPointXY(vertices[0]), QgsPointXY(vertices[-1])
        if len(vertices) > 2 and primeiro == ultimo:
            pontos.extend(QgsPointXY(v) for v in vertices)
        else:
            pontos.extend([primeiro, ultimo])
    return [QgsGeometry.fromPointXY(p) for p in pontos]


def intersecao_interna(linha, geometria, tol):
    """Distâncias, ao longo de ``linha`` (``QgsGeometry`` de linha), das
    interseções **internas** (``tol < d < comprimento - tol``) com uma única
    ``geometria`` já pronta para comparar (ex.: já reduzida à borda, se for o
    caso). Ordenadas; não trata duplicatas — isso é responsabilidade de quem
    agrega múltiplas geometrias.

    Além da interseção exata do GEOS, também conta como ponto de interseção
    um **quase toque** — qualquer ponto de uma geometria a ``tol`` ou menos
    do traçado da outra, mesmo sem o predicado exato do GEOS reconhecer:
    caso degenerado (ponto efetivamente sobre a linha, a menos de ruído de
    ponto flutuante) em que ``intersects()`` pode falhar por imprecisão
    numérica mesmo a uma distância real irrisória. Testa a ponta de
    ``geometria`` contra o traçado de ``linha`` (cobre uma geometria
    candidata cuja ponta encosta no meio de ``linha``) e **cada vértice**
    de ``linha`` — não só suas pontas — contra o traçado de ``geometria``
    (cobre um vértice interno de ``linha`` encostando em qualquer ponto de
    ``geometria``, vértice ou meio de aresta). Uma ponta da própria
    ``linha`` nunca gera um ponto de interseção **interno** — por definição
    fica sempre em ``d = 0`` ou ``d = comprimento``, fora do intervalo — o
    filtro final já descarta essas sem precisar de um caso especial.
    """
    comprimento = linha.length()
    distancias = []

    inter = linha.intersection(geometria)
    if not inter.isEmpty():
        for v in inter.vertices():
            distancias.append(
                linha.lineLocatePoint(QgsGeometry.fromPointXY(QgsPointXY(v)))
            )

    for ponta in _pontas(geometria):
        if linha.distance(ponta) <= tol:
            distancias.append(linha.lineLocatePoint(ponta))

    for v in linha.vertices():
        ponto = QgsGeometry.fromPointXY(QgsPointXY(v))
        if geometria.distance(ponto) <= tol:
            distancias.append(linha.lineLocatePoint(ponto))

    return sorted(d for d in distancias if tol < d < comprimento - tol)


def distancias_de_intersecao_interna(linha, geometrias, tol):
    """Distâncias (ao longo de ``linha``, ordenadas e sem duplicatas dentro de
    ``tol``) das interseções internas entre ``linha`` e cada geometria de
    ``geometrias`` — um iterável de ``QgsGeometry`` já prontas para comparar.
    Não faz nenhuma leitura de camada: quem monta ``geometrias`` decide a
    fonte (camada de quebra auxiliar, ou trechos já carregados em memória).
    """
    distancias = []
    for g in geometrias:
        distancias.extend(intersecao_interna(linha, g, tol))
    distancias.sort()
    unicas = []
    for d in distancias:
        if not unicas or d - unicas[-1] > tol:
            unicas.append(d)
    return unicas


def cortar(coords, distancias, tol):
    """Divide a polilinha ``coords`` nas ``distancias`` (ao longo da linha,
    já ordenadas e sem duplicatas dentro de ``tol``).

    Devolve uma lista de listas de ``QgsPointXY``. O primeiro pedaço fica no
    registro original; os demais viram registros novos. Sem ``distancias``,
    devolve ``[coords]``.
    """
    if not distancias:
        return [coords]

    linha = QgsGeometry.fromPolylineXY(coords)
    comprimento = linha.length()
    curva = linha.constGet()
    cortes = [0.0] + list(distancias) + [comprimento]
    pedacos = []
    for a, b in zip(cortes, cortes[1:]):
        if b - a <= tol:
            continue
        sub = curva.curveSubstring(a, b)
        if sub is None:
            continue
        pts = [QgsPointXY(v) for v in QgsGeometry(sub.clone()).vertices()]
        if len(pts) >= 2:
            pedacos.append(pts)
    return pedacos or [coords]


def _geometrias_de_camadas(camadas, bbox):
    """Geometrias das feições das ``camadas`` cujo bbox intersecta ``bbox``,
    já reduzidas à borda quando poligonais."""
    for camada in camadas:
        pedido = QgsFeatureRequest().setFilterRect(bbox)
        for f in camada.getFeatures(pedido):
            g = f.geometry()
            if g is None or g.isEmpty():
                continue
            yield _fronteira(g)


def _distancias_de_quebra(linha, camadas_quebra, tol):
    bbox = linha.boundingBox()
    return distancias_de_intersecao_interna(
        linha, _geometrias_de_camadas(camadas_quebra, bbox), tol
    )


def quebrar(coords, camadas_quebra, tol):
    """Divide a polilinha ``coords`` nas interseções internas com as camadas.

    Devolve uma lista de listas de ``QgsPointXY``. O primeiro pedaço fica no
    registro original; os demais viram registros novos. Sem camadas, devolve
    ``[coords]``.
    """
    if not camadas_quebra:
        return [coords]

    linha = QgsGeometry.fromPolylineXY(coords)
    distancias = _distancias_de_quebra(linha, camadas_quebra, tol)
    return cortar(coords, distancias, tol)
