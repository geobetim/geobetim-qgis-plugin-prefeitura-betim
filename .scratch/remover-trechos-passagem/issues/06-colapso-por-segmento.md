# 06: Colapsar o segmento de passagem inteiro (correção do 5321)

**What to build:** o algoritmo "Remover trechos de passagem" passa a colapsar o
**segmento de passagem** inteiro num trecho só, em vez de remover só o trecho com
as duas pontas em nó de passagem e estender um vizinho. Depois de um "remover +
estender", o resultado ainda podia encostar noutro nó de passagem e ficar como
dois trechos onde não há cruzamento nenhum — foi o que aconteceu no
`COD_LOGRADOURO 5321` (o trecho `IDPKTRLOGR 16245` foi removido, `12330` e `16244`
sobraram separados, sem cruzamento entre eles).

**Blocked by:** 03, 04, 05

**Status:** done

_`identificacao.py` reescrito (`segmentos_de_passagem`, `_no_de_passagem` com
`nos_bloqueados`, `_ordenar`). `absorcao.py` reescrito (`colapsar`; `_maior`
empate → menor id; sai `planejar`/`_componentes`/`_externos`/`_incorporar`).
`quebra.py` ganhou `nos_tocados_por_quebra` (fase 1). `algoritmo.py`: fase 1 usa
segmentos + `nos_bloqueados`, resumo por "segmentos colapsados". `CONTEXT.md` e
`spec.md` atualizados. Testes funcionais com stub: A–B–C–D → 1; 5321
(`12330/16245/16244`) → 1 (sobrevive `16244`); cruzamento/quebra no nó → parte em
2 segmentos que colapsam; anel → 1 fechado; empate de comprimento → menor id;
segmento de 1 trecho → intocado._

## Comportamento

- **Fase 1 — colapso.** Para cada `COD_LOGRADOURO` em escopo, encontra os
  **segmentos de passagem** (sequência maximal de trechos do mesmo código ligados
  só por **nós de passagem**; termina em cruzamento, bifurcação ou extremidade).
  Todo segmento de passagem com **2+ trechos** colapsa: sobrevive o **maior por
  `QgsGeometry.length()`** (empate → **menor** `IDPKTRLOGR`), estendido por todos
  os vértices dos demais na ordem do segmento; os outros são apagados.
- **Nó de passagem** agora exige também: nenhuma feição de **camada de quebra
  1/2** encosta no nó (dentro da tolerância de encaixe). Feição de quebra no nó →
  cruzamento → o segmento para ali.
- **Fase 2 — quebra.** Inalterada em intenção: divide cada trecho colapsado nas
  interseções **internas** (`tol < d < comprimento − tol`) com as camadas de
  quebra; registro original fica com o 1º pedaço, cada pedaço seguinte vira
  registro novo (`IDPKTRLOGR` da sequência do Geomedia / nulo + aviso).
- **Não apaga/recria à toa:** trecho que é um segmento de um trecho só, sem
  cruzamento novo de camada de quebra no interior, fica **intacto** — mesma
  feição, mesmo `IDPKTRLOGR`, mesma geometria.

## Acceptance criteria

- [x] `identificacao.py` passa a devolver **segmentos de passagem** (listas de ids
      de trecho, tamanho ≥ 2), não "trechos de passagem" avulsos. O teste de nó de
      passagem considera as camadas de quebra como cruzamento.
- [x] `absorcao.py` colapsa cada segmento: escolhe o maior (empate → menor id),
      estende por todos os vértices dos demais, devolve `geom_nova` + `apagar`.
      Sai a lógica de "maior vizinho externo por lado" e a divisão no meio da
      cadeia.
- [x] `algoritmo.py`: fase 1 recebe as camadas de quebra para o teste de nó;
      fase 2 (quebra) roda depois, sobre os trechos colapsados, como já está.
- [x] `A—B—C—D` com todos os nós internos de passagem → **1 trecho** (não 2).
- [x] `COD_LOGRADOURO 5321`: o segmento `12330 — 16245 — 16244` vira **1 trecho**
      (o maior dos três, estendido pelos outros dois; os outros dois apagados).
- [x] Camada de quebra passando por um nó de um segmento → o segmento para nesse
      nó; os dois lados **não** colapsam. Lógica de consumo (`nos_bloqueados` em
      `segmentos_de_passagem`) testada com stub; o produtor
      `nos_tocados_por_quebra` (distância feição↔nó) é só `py_compile` — checar no
      QGIS.
- [x] Camada de quebra cruzando o **meio** de um segmento → o segmento colapsa e
      o trecho colapsado é recortado no ponto do cruzamento — reaproveita
      `quebrar` (fase 2) do ticket 04, já testado com stub.
- [x] Segmento de um trecho só, sem quebra interna → trecho intacto, mesmo
      `IDPKTRLOGR`.
- [x] Anel fechado (segmento que é o logradouro inteiro, sem cruzamento) → colapsa
      no maior trecho, geometria fecha.
- [x] Resumo no log: "segmento(s) de passagem colapsado(s)", "trecho(s)
      apagado(s)", "registro(s) novo(s) pela quebra", "logradouro(s) pulado(s)".
- [x] `CONTEXT.md` atualizado (**Segmento de passagem**, **Trecho absorvedor**,
      **Remoção de trecho de passagem**, **Camada de quebra**, **Nó de passagem**,
      **Cruzamento**) — já feito na modelagem.
- [x] Spec `.scratch/remover-trechos-passagem/spec.md` atualizada nas seções que
      descreviam a absorção por vizinho.
- [x] `python -m py_compile` limpo; testes funcionais de `identificacao`/
      `absorcao` cobrindo os cenários acima.
- [ ] Verificação do operador no QGIS 3.28 sobre o `5321` real. (pendente)
