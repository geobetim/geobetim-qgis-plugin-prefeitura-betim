# Spec: Remover trechos de passagem (plugin do QGIS)

**Status:** implementado (tickets 01–10); verificação do operador no QGIS 3.28
pendente. O ticket **06** (colapso por segmento) revê a absorção; o ticket
**07** corrige a camada de quebra poligonal (borda, não área) e desamarra a fase
2 da fase 1; o ticket **08** corrige a resolução de owner Oracle (nunca
adivinhar via `CURRENT_SCHEMA`) e o desempate do absorvedor pela chave
configurada; o ticket **09** torna visível o descarte por "já numerado", checa
o retorno das escritas na camada e desconsidera `COD_LOGRADOURO` nulo; o
ticket **10** sincroniza esta spec, o ADR-0005 e o `metadata.txt`. O colapso de
**segmento fechado** (anel) foi corrigido em spec própria,
`.scratch/segmento-fechado/`. Uma nova **fase 0** — a própria camada de
trechos como fonte obrigatória de cruzamento entre `COD_LOGRADOURO`
diferentes, antes do colapso — foi acrescentada em spec própria,
`.scratch/quebra-entre-logradouros/` (ADR-0006); o "Fluxo de execução" abaixo
já reflete o modelo de três fases.

> **Revisão do ticket 06 (correção do `COD_LOGRADOURO 5321`).** A unidade da
> operação passou de "trecho com as duas pontas em nó de passagem" para o
> **segmento de passagem** inteiro: todo segmento de 2+ trechos ligados só por nós
> de passagem colapsa num trecho só (o maior; empate → **menor** `IDPKTRLOGR`).
> Sai a lógica de "maior vizinho externo por lado" e a divisão no meio da cadeia;
> `A—B—C—D` com nós internos de passagem passa a dar **1 trecho**, não 2. As
> camadas de quebra também viram fonte de cruzamento na identificação. As User
> Stories 8, 11, 13, 15 e o cenário "A—B—C—D → 2 trechos" das Testing Decisions
> ficam substituídos por este modelo.

## Problem Statement

A camada de trechos-logradouros tem super-segmentação: trechos curtos espremidos
entre dois **nós de passagem**, sem nenhum **cruzamento** nem **extremidade**
encostado, que não deveriam ser registros separados. Hoje o cadastrador precisa
apagar cada um desses trechos na mão e ainda esticar um vizinho para tapar o vão,
vértice por vértice, para a via não ficar com buraco. É lento, sujeito a erro, e
quando a via está num banco Oracle escrito pelo Geomedia qualquer registro novo
precisa de uma chave primária que o QGIS não sabe gerar.

## Solution

Um segundo algoritmo do Processing no **conjunto de algoritmos da Prefeitura de
Betim** (mesmo plugin da **numeração automática**), "Remover trechos de
passagem", que roda sobre uma camada de linhas do projeto:

- O operador escolhe a camada de trechos, o atributo de agrupamento
  (`COD_LOGRADOURO`), a tolerância de encaixe de vértices (default 0,05 m), e —
  opcionalmente — até duas **camadas de quebra** e o atributo da chave primária
  gerada pelo Geomedia.
- Sem "apenas feições selecionadas", processa **todos os `COD_LOGRADOURO`
  distintos** da camada; com ele, só os `COD_LOGRADOURO` presentes entre os
  trechos selecionados.
- Identifica topologicamente os **segmentos de passagem** de cada
  `COD_LOGRADOURO` — sequências de trechos ligados só por **nós de passagem** — e
  colapsa cada segmento de 2+ trechos num só: sobrevive o maior por comprimento
  (empate → menor `IDPKTRLOGR`), estendido por todos os vértices dos demais; os
  outros são apagados. A via fica sem buraco e sem junção sem cruzamento.
- As **camadas de quebra** têm dois papéis: na identificação, feição de quebra
  encostando num nó torna esse nó cruzamento (o segmento para ali, o que preserva
  trechos já partidos no lugar certo); depois do colapso, interseções internas de
  feição de quebra com um trecho colapsado o dividem — o registro original fica
  com o primeiro pedaço, cada pedaço seguinte vira um registro novo, cópia dos
  atributos, com `IDPKTRLOGR` da sequência do Geomedia (camada Oracle + dicionário
  resolve) ou nulo, com aviso.
- Não apaga/recria à toa: um trecho já bem delimitado (segmento de um trecho só,
  sem cruzamento novo de camada de quebra no interior) fica intacto — mesma
  feição, mesmo `IDPKTRLOGR`, mesma geometria.
- Tudo é aplicado **na edição** da camada, sem `commitChanges()` — os resultados
  ficam visíveis no mapa e na tabela, e só vão ao banco quando o operador clica
  em "Salvar edições da camada"; "Reverter" desfaz tudo num passo.
- Ao fim, um resumo: trechos de passagem removidos, absorvedores estendidos,
  registros novos da quebra, quantos ficaram sem `IDPKTRLOGR`, `COD_LOGRADOURO`
  pulados com aviso.

Como a remoção muda a geometria dos trechos e deixa a numeração anterior
obsoleta, o algoritmo de **numeração automática** ganha um parâmetro
**"Sobrescrever numeração"** (desligado por padrão) que força a renumeração de um
`COD_LOGRADOURO` mesmo com o **número sequencial do trecho** já preenchido.

## User Stories

1. Como cadastrador, quero um algoritmo "Remover trechos de passagem" no
   Processing Toolbox, no mesmo grupo "Trecho logradouro" da numeração, para usar
   como qualquer outra ferramenta do QGIS.
2. Como cadastrador, quero escolher a camada de trechos num seletor de camada de
   linha do projeto.
3. Como cadastrador, quero informar o atributo de agrupamento (`COD_LOGRADOURO`)
   num seletor de campo da camada, análogo ao da numeração.
4. Como cadastrador, quero informar a tolerância de encaixe de vértices, com
   0,05 m já preenchido como padrão.
5. Como cadastrador, quero, sem seleção ativa, processar todos os
   `COD_LOGRADOURO` distintos da camada de uma vez.
6. Como cadastrador, quero, com trechos selecionados e a opção "apenas
   selecionadas" ligada, processar apenas os `COD_LOGRADOURO` presentes nessa
   seleção.
7. Como cadastrador, quero um erro claro se ligar "apenas selecionadas" sem nada
   selecionado.
8. Como cadastrador, quero que um trecho seja considerado **trecho de passagem**
   só quando **ambas** as pontas são **nós de passagem** — grau 2 no grafo do
   `COD_LOGRADOURO`, exatamente dois trechos do mesmo código no nó, nenhum outro
   `COD_LOGRADOURO` incidente, sem bifurcação.
9. Como cadastrador, quero que a identificação dos trechos de passagem seja
   topológica, sem depender de nenhum atributo de tipo/classe.
10. Como cadastrador, quero que o conjunto de trechos de passagem seja
    identificado de uma vez, sobre o grafo original, antes de qualquer edição.
11. Como cadastrador, quero que cada trecho de passagem apagado seja coberto pelo
    **trecho absorvedor**: o maior vizinho (por `QgsGeometry.length()`) do mesmo
    `COD_LOGRADOURO` que não esteja ele mesmo sendo removido; empate pelo maior
    `IDPKTRLOGR`/id.
12. Como cadastrador, quero que a geometria do absorvedor seja estendida para
    passar por **todos** os vértices do trecho removido, na ordem, sem duplicar o
    nó compartilhado.
13. Como cadastrador, quero que, numa cadeia de trechos de passagem sem nenhum
    vizinho externo, o maior trecho da própria cadeia seja mantido e absorva os
    demais.
14. Como cadastrador, quero que os demais trechos que tocavam o nó do trecho
    removido passem a tocar o absorvedor naturalmente (a topologia cicatriza).
15. Como cadastrador, quero que o exemplo `A—B—C—D` com nós internos de passagem
    (B e C são trechos de passagem) resulte em dois trechos: `A` estendido por
    `B` e `D` estendido por `C`, encontrando-se no antigo nó `B–C`.
16. Como cadastrador, quero que um `COD_LOGRADOURO` seja pulado com aviso quando
    um trecho de passagem tem menos de 2 vértices, quando o absorvedor
    compartilha as duas pontas do removido (laço), ou quando não há vizinho do
    mesmo código.
17. Como cadastrador, quero que os atributos do absorvedor não sejam alterados —
    só a geometria dele muda.
18. Como cadastrador, quero informar opcionalmente até duas **camadas de quebra**
    (linha ou polígono) do projeto.
19. Como cadastrador, quero que, com camadas de quebra informadas, cada
    absorvedor já estendido seja dividido nos pontos onde cruza essas camadas
    (união das duas), **internos** ao traçado, não nas extremidades.
20. Como cadastrador, quero que a quebra use o recurso nativo de divisão de linha
    do QGIS, não um cálculo próprio de interseção.
21. Como cadastrador, quero que, na quebra, o registro original fique com o
    primeiro pedaço e cada pedaço seguinte vire um registro novo, cópia de todos
    os atributos do original.
22. Como cadastrador, quero que pedaços degenerados da quebra (menos de 2
    vértices ou comprimento ~0) sejam descartados com aviso.
23. Como cadastrador, quero que os registros novos da quebra **nunca** herdem o
    `IDPKTRLOGR` do trecho original.
24. Como cadastrador, quero informar opcionalmente o atributo que é a chave
    primária auto-incremental do Geomedia (`IDPKTRLOGR`), efetivo só quando a
    camada é do provider Oracle.
25. Como cadastrador, quero que, com esse atributo informado e a camada Oracle, o
    algoritmo descubra `OWNER` e `TABLE_NAME` pelo próprio data source da camada
    e `COLUMN_NAME` pelo campo escolhido.
26. Como cadastrador, quero que o algoritmo consulte `GDOSYS.GFIELDMAPPING` por
    esses três campos e, se obtiver exatamente uma linha com `SEQUENCE_OWNER` e
    `SEQUENCE_NAME` preenchidos, preencha cada registro novo com o próximo valor
    dessa sequência.
27. Como cadastrador, quero que os N valores da sequência sejam obtidos numa
    única consulta, não um a um.
28. Como cadastrador, quero que qualquer outro caso (parâmetro vazio, camada
    não-Oracle, zero ou mais de uma linha em `GFIELDMAPPING`, colunas de
    sequência nulas, falha de conexão) deixe os registros novos com `IDPKTRLOGR`
    nulo e um aviso com a contagem e o motivo.
29. Como cadastrador, quero que todas as mudanças entrem na **edição** da camada
    (`startEditing` se preciso, um único `beginEditCommand`/`endEditCommand`,
    `triggerRepaint`), sem `commitChanges()`.
30. Como cadastrador, quero poder inspecionar o resultado no mapa e reverter tudo
    num único passo de desfazer antes de salvar.
31. Como cadastrador, quero que, se a camada for de banco, nada vá ao banco até
    eu clicar em "Salvar edições da camada".
32. Como cadastrador, quero um resumo ao fim: trechos de passagem removidos,
    absorvedores estendidos, registros novos criados pela quebra, quantos
    ficaram sem `IDPKTRLOGR`, quantos `COD_LOGRADOURO` pulados e por quê, mais
    uma linha lembrando de salvar/reverter.
33. Como cadastrador, quero que o algoritmo recuse uma camada em CRS geográfico
    (graus), com mensagem pedindo reprojeção para CRS métrico — o comprimento e a
    tolerância são planares e em metros.
34. Como cadastrador, quero barra de progresso e cancelamento, aproveitando o
    feedback nativo do Processing.
35. Como cadastrador, quero que o algoritmo não altere o **número sequencial do
    trecho** de nada — isso é papel da numeração.
36. Como cadastrador da numeração, quero um parâmetro "Sobrescrever numeração" no
    algoritmo de numeração, desligado por padrão, que quando ligado renumera um
    `COD_LOGRADOURO` mesmo com o número sequencial já preenchido em algum trecho.
37. Como cadastrador da numeração, quero que "Sobrescrever numeração" desligado
    mantenha exatamente o comportamento atual (ignora logradouro já numerado).
38. Como cadastrador, quero rodar "Remover trechos de passagem" e depois a
    numeração com "Sobrescrever numeração" ligado para reconciliar a numeração
    dos `COD_LOGRADOURO` que tiveram geometria alterada.
39. Como mantenedor, quero o plugin numa pasta `plugin-qgis/prefeitura_betim/`,
    com um único provider ("Prefeitura de Betim") expondo os dois algoritmos.
40. Como mantenedor, quero o código de cada algoritmo num subpacote próprio
    (`numeracao_trecho_logradouro/`, `remocao_trecho_logradouro_passagem/`) e o
    que é compartilhado em `shared/`, com `shared/` sem importar dos subpacotes
    de algoritmo e os algoritmos sem importar um do outro.
41. Como mantenedor, quero `metadata.txt` descrevendo o plugin como "Conjunto de
    algoritmos da Prefeitura de Betim", `qgisMinimumVersion=3.28`, autor
    "Prefeitura de Betim", email `tuffisal@gmail.com`, `hasProcessingProvider=yes`.
42. Como mantenedor, quero que as primitivas geométricas usem recursos nativos do
    QGIS (distância, vetor, índice espacial, iteração de vértices, divisão de
    linha), não funções próprias.
43. Como mantenedor, quero um ADR registrando por que o `IDPKTRLOGR` de trechos
    novos é resolvido pelo dicionário `GDOSYS.GFIELDMAPPING` do Geomedia.
44. Como mantenedor, quero que o código Python passe em `py_compile` e carregue
    sem erro no QGIS 3.28, com o provider mostrando os dois algoritmos.
45. Como mantenedor do glossário, quero os termos **Trecho de passagem**,
    **Trecho absorvedor**, **Remoção de trecho de passagem**, **Camada de
    quebra** e **Sobrescrever numeração** no `CONTEXT.md` (já adicionados na
    modelagem) refletidos no spec.

## Implementation Decisions

### Prefactor — reestruturação do plugin

- Renomear `plugin-qgis/numeracao_trechologradouro/` para
  `plugin-qgis/prefeitura_betim/` (nome válido como módulo Python), mantendo o
  mesmo `QgsProcessingProvider` "Prefeitura de Betim".
- Subpacotes dentro do plugin:
  - `shared/` — utilidades compartilhadas. Nunca importa dos subpacotes de
    algoritmo. Contém: índice de nós por tolerância de encaixe + grau do nó +
    trechos incidentes no nó (hoje embutido no grafo da numeração); checagem de
    CRS métrico e leitura da camada inteira para estruturas em memória + índice
    espacial (hoje inline no algoritmo de numeração); wrapper de edição
    ("põe em edição, `beginEditCommand`, aplica, `endEditCommand`,
    `triggerRepaint`, sem `commitChanges`").
  - `numeracao_trecho_logradouro/` — o algoritmo de numeração atual. O
    `QgsProcessingAlgorithm` (hoje no topo do pacote) passa para dentro deste
    subpacote; o grafo/sequenciador/atribuidor/erros acompanham; o grafo passa a
    montar-se sobre o índice de nós de `shared/`.
  - `remocao_trecho_logradouro_passagem/` — o algoritmo novo, com o
    `QgsProcessingAlgorithm`, a identificação topológica, a absorção/extensão, a
    quebra pelas camadas auxiliares e a resolução de sequência do Geomedia.
- Os subpacotes de algoritmo importam de `shared/`, nunca um do outro.
- `provider.py` importa e adiciona os dois algoritmos.
- `metadata.txt`: `description`/`about` passam a descrever "Conjunto de algoritmos
  da Prefeitura de Betim para edição da camada de trechos-logradouros";
  `version` incrementada; demais chaves preservadas.

### Identidade do algoritmo novo

- `name` = `remover_trechos_passagem`; `displayName` = "Remover trechos de
  passagem"; `group` = "Trecho logradouro" / `groupId` = `trechologradouro`.
- `flags` inclui `FlagNoThreading` (grava direto na camada do projeto).

### Parâmetros do algoritmo novo

- Camada de trechos: seletor de camada vetorial de linha, gravável, do projeto
  (mesma escolha do algoritmo de numeração — não usar `FeatureSource`, que
  devolve `None` no modo "apenas selecionadas").
- "Processar apenas os `COD_LOGRADOURO` das feições selecionadas": booleano,
  default **`True`** (o operador desmarca para processar a camada inteira —
  revisto a pedido do operador, era `False`); ligado sem seleção → erro claro.
- Atributo de agrupamento (`COD_LOGRADOURO`): seletor de campo, parentLayer = a
  camada, tipo qualquer.
- Tolerância de encaixe de vértices (m): número Double, default `0.05`, mínimo 0.
- Camada de quebra 1 e Camada de quebra 2: seletores de camada vetorial
  (linha/polígono), ambos opcionais.
- Atributo da chave primária Geomedia (`IDPKTRLOGR`): seletor de campo opcional,
  parentLayer = a camada, marcado como avançado. Efetivo só quando
  `camada.dataProvider().name() == 'oracle'`; ignorado com aviso caso contrário
  (o Processing não tem "habilitar se" nativo, então o parâmetro fica sempre
  presente e o algoritmo decide em runtime).
- Sem parâmetro de saída — grava na camada de entrada.

### Fluxo de execução do algoritmo novo

1. Valida o CRS da camada como projetado com unidade em metros (via `shared/`);
   senão `QgsProcessingException` pedindo reprojeção.
2. Lê **todas** as feições de linha para estruturas em memória: por feição, id,
   valor do campo de agrupamento, geometria; monta um índice espacial das
   feições.
3. Determina os `COD_LOGRADOURO` em escopo: distintos de toda a camada, ou — com
   "apenas selecionadas" — os das feições em `selectedFeatureIds()`.
4. Monta as estruturas em memória da vizinhança (feições cujo bbox intersecta o
   bbox dos trechos em escopo expandido pela tolerância) — ainda sem montar o
   índice de nós.
5. **Fase 0 — quebra pela própria camada (cruzamento entre logradouros)** —
   sempre, sem parâmetro (`.scratch/quebra-entre-logradouros/`, ADR-0006): para
   cada trecho em escopo, acha os pontos onde ele cruza — com ou sem nó
   compartilhado hoje, inclusive um X sem vértice em nenhum dos dois lados — um
   trecho de **outro** `COD_LOGRADOURO` na vizinhança (sempre linha contra
   linha) e o divide ali; o outro `COD_LOGRADOURO` nunca é tocado, mesmo fora
   de escopo. Cruzamento entre trechos do **mesmo** `COD_LOGRADOURO` sem nó
   compartilhado também divide, desde a revisão do ADR-0007 (antes, era
   tratado como atípico: não dividia, só avisava no log — ver
   `.scratch/quase-toque-cruzamento/`). A detecção compara
   sempre contra a topologia original (nunca o resultado já cortado de outro
   trecho do mesmo laço). Um pedaço novo entra com um identificador temporário
   (nunca um id real de feição) e tem sua chave primária resolvida na hora,
   pelo mesmo pipeline do Geomedia (ADR-0005) — o valor já entra no desempate
   do absorvedor da fase 1.
6. Monta o índice de nós **sobre a topologia pós-fase-0**: nós = pontas de
   trecho (reais e os pedaços novos da fase 0) agrupadas pela tolerância de
   encaixe; por nó, grau e conjunto de `COD_LOGRADOURO` incidentes e trechos
   incidentes. O nó de cada corte da fase 0 é marcado cruzamento
   explicitamente (não depende de o outro código ter, ele também, um nó real
   ali). O teste de **nó de passagem** também exige que nenhuma feição de
   **camada de quebra** encoste no nó (dentro da tolerância de encaixe) —
   feição de quebra no nó → cruzamento.
7. **Fase 1 — colapso do segmento** — para cada `COD_LOGRADOURO` em escopo, no
   grafo restrito a esse código, monta os **segmentos de passagem**: sequências
   maximais de trechos ligados só por nós de passagem, terminadas em cruzamento /
   bifurcação / extremidade. Todo segmento com **2+ trechos** colapsa:
   - sobrevive o **trecho absorvedor** = o de maior `QgsGeometry.length()` do
     segmento; empate → **menor** `IDPKTRLOGR`;
   - a geometria do absorvedor é estendida para passar por **todos** os vértices
     dos demais trechos do segmento, na ordem do segmento, ligando pela ponta
     comum, sem duplicar o nó; os demais são apagados;
   - só a geometria do absorvedor muda; atributos preservados; número sequencial
     não é tocado;
   - pula com aviso: trecho do segmento com < 2 vértices, ou segmento que não
     encadeia numa polilinha única.
   - **segmento fechado** (anel — as duas pontas do segmento caem no mesmo nó):
     o absorvedor vira um trecho fechado que **começa e termina no nó de
     fechamento** (em geral um cruzamento, ex.: o toco `29810` no
     `COD_LOGRADOURO 7542`); a emenda orienta o primeiro trecho por esse nó e os
     seguintes pela ponta comum, sem depender da orientação da geometria do
     absorvedor no banco (spec `.scratch/segmento-fechado/`).
   - O conjunto de segmentos é fixado aqui, sobre o grafo original.
8. **Segmento de um trecho só** — não é segmento de passagem; o trecho fica
   intacto (mesma feição, mesmo `IDPKTRLOGR`), a menos que a fase 0 já o tenha
   dividido, ou a fase 2 encontre um cruzamento novo de camada de quebra no
   seu interior.
9. **Fase 2 — quebra** — se camadas de quebra informadas, para **todo trecho em
   escopo**, colapsado (geometria já estendida) ou não (geometria original) —
   não depende de a fase 1 ter colapsado algo: coleta os pontos de interseção
   internos (`tol < d < comprimento − tol`) com a união das camadas de quebra
   (feição poligonal conta pela **borda**, não pela área); divide a geometria
   nesses pontos com o recurso nativo do QGIS; o registro original fica com o 1º
   pedaço, cada pedaço seguinte vira registro novo (cópia de todos os atributos
   do original, menos `IDPKTRLOGR`); descarta pedaços degenerados com aviso.
   Interseção que cai num limite de trecho já existente não gera recorte.
10. **`IDPKTRLOGR` dos registros novos da fase 2** — sempre nulado primeiro. Se o parâmetro
   da chave primária foi informado e a camada é Oracle:
   - deriva `OWNER`/`TABLE_NAME` do data source da camada decodificado pelo
     próprio provider Oracle (`decodeUri`); **nunca adivinha** o owner pelo
     schema da sessão — sem owner/tabela, chave nula com aviso, sem nenhuma
     consulta ao banco; `COLUMN_NAME` = o campo escolhido; os três em
     maiúsculas;
   - consulta, pela conexão do provider Oracle da camada,
     `SELECT SEQUENCE_OWNER, SEQUENCE_NAME FROM GDOSYS.GFIELDMAPPING
     WHERE OWNER = :o AND TABLE_NAME = :t AND COLUMN_NAME = :c`;
   - exatamente uma linha com `SEQUENCE_OWNER`/`SEQUENCE_NAME` preenchidos →
     obtém os N valores numa consulta só
     (`SELECT "<owner>"."<seq>".NEXTVAL FROM DUAL CONNECT BY LEVEL <= :n`) e
     atribui aos N registros novos;
   - qualquer outro caso → registros novos com `IDPKTRLOGR` nulo + aviso com
     contagem e motivo.
11. **Aplicação na edição** — `startEditing()` se preciso; um `beginEditCommand`;
    ordem: alterar a geometria dos ids reais (absorvedores, e qualquer id real
    que a fase 0 truncou, mesmo sem mais nenhuma mudança depois) → adicionar
    os registros novos (os pedaços da fase 0 que sobreviveram à fase 1, e os
    da quebra por camada de quebra) → apagar os trechos reais (um id
    temporário da fase 0 que a fase 1 absorveu é só descartado — nunca chama
    `deleteFeature`, porque nunca existiu na camada); `endEditCommand`;
    `triggerRepaint`. Sem `commitChanges()`. Erro no meio → `destroyEditCommand()`
    e re-lança. Cada escrita tem o retorno checado: uma recusa do QGIS vira erro
    (comando destruído, nada gravado pela metade) — o resumo nunca diz
    "gravado" sem ter gravado.
12. Resumo no `feedback`: uma linha própria da fase 0 (trechos divididos,
    registros novos com/sem chave), e a linha já existente com segmentos de
    fato colapsados (não os identificados — segmento pulado por aviso fica de
    fora), trechos apagados (reais), registros novos da fase 2 (com/sem
    chave), logradouros com segmento, `COD_LOGRADOURO` pulados (com motivo), e
    a linha de salvar/reverter.
13. **`COD_LOGRADOURO` nulo** — trecho sem código de logradouro é desconsiderado
    por completo já na leitura: fora de escopo, fora do grafo, não é cruzamento
    para ninguém (nem candidato de cruzamento da fase 0). O log avisa quantos
    foram desconsiderados.

### Mudança no algoritmo de numeração (ticket próprio)

- Novo parâmetro booleano "Sobrescrever numeração" no `QgsProcessingAlgorithm` da
  numeração, default `False`.
- `False` → comportamento atual: `COD_LOGRADOURO` com número sequencial não-NULL
  em ao menos um trecho é ignorado.
- `True` → a etapa de descarte é pulada; todo `COD_LOGRADOURO` em escopo é
  renumerado e o número sequencial sobrescrito onde já havia valor.
- `shortHelpString`/`about` citam a opção; nenhuma outra mudança de
  comportamento.

### Documentação

- Novo ADR (`docs/adr/0005`): resolução do `IDPKTRLOGR` de trechos novos pelo
  dicionário `GDOSYS.GFIELDMAPPING` do Geomedia. Trade-off: acopla o plugin ao
  esquema interno do Geomedia versus a alternativa (deixar a PK nula, que quebra
  a constraint no commit, ou um max+1 local, que colide com a sequência real e
  com concorrência).
- `CONTEXT.md`: termos **Trecho de passagem**, **Trecho absorvedor**, **Remoção
  de trecho de passagem**, **Camada de quebra**, **Sobrescrever numeração** e as
  revisões de **`IDPKTRLOGR`** e **Plugin do QGIS** já adicionados na modelagem.
- ADR-0004 permanece válido — este trabalho não muda regra de numeração; só
  acrescenta um algoritmo ao mesmo plugin e uma opção ao algoritmo existente.

## Testing Decisions

- **Sem suíte automatizada no repositório**, consistente com as rodadas
  anteriores do plugin: o núcleo depende de tipos do `qgis.core`
  (`QgsGeometry`, `QgsSpatialIndex`, `QgsVector`, divisão nativa de linha) e a
  resolução de sequência depende de uma conexão Oracle viva — nada disso roda
  fora do QGIS. Um bom teste aqui verifica **comportamento externo** (o que
  aconteceu com as feições da camada), não a estrutura interna dos módulos.
- **Seam de verificação — sintaxe e estrutura**: `python -m py_compile` em todos
  os `.py` do plugin; o provider carrega no QGIS 3.28 mostrando os **dois**
  algoritmos, cada um com `initAlgorithm`/`processAlgorithm` válidos.
- **Seam de verificação — comportamento** (operador, QGIS 3.28, camada real de
  trechos):
  - um trecho de passagem conhecido some da camada; o maior vizinho do mesmo
    `COD_LOGRADOURO` passa a cobrir o traçado dele, com todos os vértices; o que
    tocava o nó do trecho removido agora toca o absorvedor;
  - a cadeia `A—B—C—D` com nós internos de passagem termina em dois trechos;
  - com uma camada de quebra cruzando o absorvedor estendido, aparece o registro
    original mais um ou mais registros novos, atributos copiados; numa camada
    Oracle com o dicionário resolvendo, os novos saem com `IDPKTRLOGR` da
    sequência; sem resolver, saem nulos e o log avisa;
  - "apenas selecionadas" restringe o efeito aos `COD_LOGRADOURO` com feição
    selecionada;
  - nada é gravado no banco até "Salvar edições da camada"; "Reverter" desfaz
    tudo num passo.
- **Seam de verificação — numeração**: rodar a numeração com "Sobrescrever
  numeração" ligado sobre um `COD_LOGRADOURO` que já tem número sequencial →
  renumera e sobrescreve; desligado → ignora, igual a hoje.
- **Prior art**: verificação por comparação direta com o dado real dentro do
  QGIS, como já feito nesta base para `.scratch/plugin-qgis/` e
  `.scratch/numeracao-em-lote/`.

## Out of Scope

- Ajustar ou limpar o **número sequencial do trecho** dos `COD_LOGRADOURO`
  afetados pela remoção — quem reconcilia é a numeração com "Sobrescrever
  numeração" numa passada posterior.
- Recalcular o `CODTRECHOLOGRADOURO` / a máscara `NNNNN.NNNN`.
- Modo por área/MBR neste algoritmo.
- Reprojeção interna de camada em CRS geográfico (só recusa com mensagem).
- Persistir no banco — o algoritmo nunca faz `commitChanges()`.
- Detecção automática de qual campo é a chave primária (sempre por parâmetro).
- Chave primária por sequência fora do dicionário `GDOSYS` (só o caminho
  `GFIELDMAPPING`); bancos que não sejam Oracle.
- Mais de duas camadas de quebra.
- Empacotamento `.zip` / publicação em repositório de plugins do QGIS.
- Testes automatizados no repositório.
- Qualquer mudança no serviço C#, na API HTTP ou no front-end web.

## Further Notes

- O QGIS MCP não estava conectado na modelagem; a versão mínima 3.28 vem do
  plugin de numeração.
- `QgsProcessingParameterField` não tem "habilitar se" nativo no Processing; o
  campo da chave primária entra como parâmetro opcional/avançado e o algoritmo só
  o consome quando o provider da camada é `oracle`, avisando quando ignorado.
- Consumir `NEXTVAL` no momento da execução (e não no commit) é intencional:
  mantém o modelo "edição sem commit", os valores ficam visíveis e revertíveis, e
  buracos na sequência são aceitáveis no Oracle.
- A ordem de aplicação das edições (alterar geometria → inserir novos → apagar)
  evita que a remoção invalide ids de feição usados na absorção.
- A camada pode ter milhares de trechos; o agrupamento de nós e o filtro de
  vizinhança usam o índice espacial para não cair em O(n²), como no plugin de
  numeração.
- A gravação na camada é a única parte destrutiva; fica sob o controle de edição
  do QGIS (undo/reverter) para o operador poder desfazer antes de salvar.
