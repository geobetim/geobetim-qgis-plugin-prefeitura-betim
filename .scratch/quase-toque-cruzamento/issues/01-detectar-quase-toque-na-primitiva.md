# 01: Detectar quase toque na primitiva de interseção interna

**What to build:** `intersecao_interna`/`distancias_de_intersecao_interna`
(`remocao_trecho_logradouro_passagem/quebra.py`) passam a reconhecer, além do
ponto de interseção exata do GEOS (`linha.intersection(geometria)`), um
"quase toque": quando a ponta de `linha` está a ≤ `tol` do traçado de
`geometria` (e simetricamente, quando a ponta de `geometria` está a ≤ `tol`
do traçado de `linha`), isso conta como um ponto de interseção interno ali —
sujeito ao mesmo filtro já existente (`tol < distância_ao_longo < comprimento
- tol`).

Sem essa correção, um ponto onde as duas geometrias praticamente se tocam
(distância real da ordem de fração de milímetro a poucos centímetros, dentro
da tolerância de encaixe configurada) pode passar batido pelo teste exato do
GEOS por imprecisão numérica — o caso real que motivou isto é o
`COD_LOGRADOURO 7640` (`IDPKTRLOGR 33729` encostando no meio do traçado de
`33725`, distância real ~4×10⁻¹⁰ m, `intersects()` devolvendo `False`), mas
uma checagem na camada inteira (16.716 trechos) encontrou **173 pares entre
`COD_LOGRADOURO` diferentes** na mesma situação — a fase 0 (quebra pela
própria camada, ADR-0006) deveria estar sempre dividindo esses casos e hoje
ignora silenciosamente.

Este ticket, isolado, já corrige a fase 0 para todo cruzamento **entre
códigos diferentes** afetado por esse problema de robustez — sem tocar na
regra do mesmo `COD_LOGRADOURO` (isso é o ticket 02). O comportamento hoje já
funcional (interseção exata, como o `7647`/`7643` do ADR-0006) não pode
mudar.

**Blocked by:** None (can start immediately)

**Status:** done

_`intersecao_interna` (`quebra.py`) passa a somar, à interseção exata do GEOS,
as pontas de `linha` e de `geometria` testadas por distância
(`linha.distance(ponta) <= tol` e vice-versa) — cada ponta que passa entra
como mais uma distância candidata, e o filtro existente
(`tol < d < comprimento - tol`) se aplica igual, no fim, a todas as
distâncias juntas (exatas + quase toque). `_pontas(geometria)` extrai o
primeiro e o último vértice como `QgsGeometry` de ponto. Testado com stub de
`qgis.core` (Shapely por baixo): 4 casos na primitiva (quase toque dentro/fora
da tolerância, quase toque perto da própria ponta filtrado, regressão da
interseção exata) + 2 na integração da fase 0 (quase toque sintético entre
códigos diferentes; regressão real do `7647`/`7643` do ADR-0006, dados do
WFS)._

- [x] `intersecao_interna` detecta um caso sintético de "quase toque" (ponta
      de uma linha a poucos milímetros do meio de outra, dentro de `tol`) como
      distância interna válida
- [x] Caso de controle: mesma configuração, mas com a ponta a uma distância
      maior que `tol` — nenhuma distância detectada
- [x] Caso de controle: quase toque a ≤ `tol`, mas caindo fora do intervalo
      interno (muito perto de uma das próprias pontas de `linha`) — continua
      filtrado pela regra `tol < d < comprimento - tol`, sem corte espúrio na
      ponta
- [x] Interseção exata do GEOS (comportamento já existente) continua
      detectando normalmente — sem regressão
- [x] Teste de integração da fase 0 com um caso sintético de quase toque
      entre `COD_LOGRADOURO` diferentes: o trecho em escopo é dividido
      corretamente
- [x] Teste de integração da fase 0 reproduzindo `COD_LOGRADOURO`
      `7647`/`7643` (ADR-0006): continua passando com o mesmo resultado de
      antes
