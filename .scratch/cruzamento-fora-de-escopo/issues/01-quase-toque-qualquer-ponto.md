# 01: Quase toque contra qualquer ponto da borda

**What to build:** `intersecao_interna`/`distancias_de_intersecao_interna`
(`quebra.py`) passam a testar cada vértice do trecho (`linha`) contra a
distância à geometria candidata inteira (`geometria.distance(vértice) <=
tol`), além do já existente (interseção exata do GEOS; vértices da
geometria candidata testados contra o traçado do trecho). Isso cobre um
vértice do trecho perto do meio de uma aresta reta de uma camada de quebra
poligonal — um caso que hoje passa batido tanto pelo teste exato do GEOS
(imprecisão numérica, mesmo problema do ADR-0007) quanto pelo teste por
vértice atual, já que a borda só tem vértices nos cantos. Vértices de
`linha` nas próprias pontas continuam sendo naturalmente filtrados pelo
intervalo interno (`tol < d < comprimento - tol`) — só vértices internos do
trecho produzem um corte válido, então isso não reintroduz o código morto
já removido antes.

Vale tanto para a fase 0 (trecho contra trecho) quanto para a fase 2
(trecho contra camada de quebra), já que as duas reaproveitam a mesma
primitiva.

**Blocked by:** None (can start immediately)

**Status:** done

_`intersecao_interna` (`quebra.py`) ganhou uma terceira fonte de distância:
cada vértice de `linha` testado por `geometria.distance(vértice) <= tol`,
convertido pra distância ao longo de `linha` via `lineLocatePoint` (exata,
já que o vértice é um ponto conhecido de `linha`). Cuidado de teste: um
"V"/"tenda" cujo vértice fica perto de uma aresta sem o caminho cruzar por
ela (senão a interseção exata do GEOS já capta, mascarando o teste) —
resolvido construindo os casos sintéticos com o pico do zigue-zague sempre
do lado de fora, a uma distância conhecida. Testado com stub de `qgis.core`
(Shapely): 6 casos (vértice interno perto do meio de uma aresta dentro/fora
da tolerância, ponta do trecho continua filtrada, regressão da direção já
existente, e os dois mesmos casos via `quebrar()`/fase 2 com uma camada de
quebra poligonal sintética). Regressão completa das rodadas anteriores
(`7640`, `7647`/`7643`, X puro, ponta a ponta fase 0+fase 1) revalidada, sem
alteração de resultado._

- [x] Caso sintético: vértice **interno** de um trecho a poucos milímetros
      do meio de uma aresta de uma geometria candidata (longe de qualquer
      vértice/canto dela), dentro da tolerância — detecta e produz uma
      distância interna válida
- [x] Caso de controle: mesma configuração, mas fora da tolerância — não
      detecta nada
- [x] Caso de controle: o vértice testado é a própria ponta do trecho
      (início ou fim) — continua filtrado pelo intervalo interno, sem corte
      espúrio
- [x] Regressão: os casos já cobertos (`7640`, `7647`/`7643`, X puro
      sintético, quase toque perto de vértice de anel fechado) continuam
      passando sem alteração de resultado
- [x] Teste de integração da fase 2 (quebra por camada de quebra): um trecho
      em escopo com um vértice interno a poucos milímetros do meio de uma
      aresta de uma camada de quebra poligonal sintética é dividido ali
