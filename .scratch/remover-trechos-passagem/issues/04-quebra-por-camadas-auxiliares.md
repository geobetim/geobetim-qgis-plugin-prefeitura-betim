# 04: Quebra do trecho absorvedor pelas camadas auxiliares

**What to build:** o operador pode informar até duas **camadas de quebra**
(linha ou polígono). Depois que um **trecho absorvedor** é estendido, se ele
cruzar alguma dessas camadas num ponto interno, é dividido ali: o registro
original fica com o primeiro pedaço e cada pedaço seguinte vira um registro novo,
cópia dos atributos do original. É o que evita um absorvedor esticado atravessar
um limite que deveria segmentá-lo.

**Blocked by:** 03

**Status:** done

_Implementado em `quebra.py` (`quebrar` via `QgsGeometry.intersection` +
`lineLocatePoint` + `QgsCurve.curveSubstring`) e no `algoritmo.py` (params
`CAMADA_QUEBRA_1/2`, criação de `QgsFeature` novos no mesmo `beginEditCommand`).
O parâmetro opcional/avançado `CAMPO_CHAVE_PRIMARIA` entrou aqui para poder
**zerar** o `IDPKTRLOGR` dos registros novos; o preenchimento pela sequência é o
ticket 05. Teste funcional de `quebrar` com stub: 1 quebra → 2 pedaços no ponto
certo; sem camada / fora do range → passthrough; 2 quebras → 3 pedaços._

- [x] Dois parâmetros opcionais "camada de quebra 1" e "camada de quebra 2"
      (camadas vetoriais de linha ou polígono do projeto).
- [x] Nenhuma das duas informada → `quebrar` devolve `[coords]`; comportamento
      idêntico ao do ticket 03.
- [x] Para cada absorvedor já estendido: coleta os pontos de interseção
      **internos** (`tol < d < comprimento - tol`) com as feições das camadas de
      quebra (`intersection`), a distância ao longo via `lineLocatePoint`, e
      recorta com `QgsCurve.curveSubstring` — nativo do QGIS.
- [x] Pedaços ordenados ao longo do traçado; o registro **original** fica com o
      1º pedaço (`changeGeometry`); cada pedaço seguinte vira um **registro
      novo** (`QgsFeature`) com cópia dos atributos do original. Com o parâmetro
      da chave primária informado, o `IDPKTRLOGR` do registro novo é zerado.
- [x] Pedaços degenerados (< 2 vértices ou faixa ≤ tol) são descartados.
- [x] As inserções entram no mesmo `beginEditCommand`, na ordem geometrias
      alteradas → registros novos → feições apagadas; sem `commitChanges()`.
- [x] O resumo no log conta os registros novos criados pela quebra.
- [x] `python -m py_compile` limpo; teste funcional de `quebrar`.
- [ ] Verificação do operador no QGIS 3.28: com uma camada de quebra cruzando um
      absorvedor estendido, aparecem o registro original mais um ou mais
      registros novos com os atributos copiados; "Reverter" desfaz tudo.
      (pendente)
