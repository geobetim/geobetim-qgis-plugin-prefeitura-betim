# Spec: Plugin do QGIS — numeração por logradouro

**Status:** done

## Problem Statement

A numeração automática só existe hoje como serviço C# atrás de HTTP, contra o
Oracle. Quem trabalha o cadastro dentro do QGIS — sobre uma camada de trechos já
carregada — não tem como numerar sem sair da ferramenta, subir o serviço e
depender do banco. Falta uma forma de rodar exatamente as mesmas regras de
numeração dentro do QGIS, escrevendo o resultado direto num atributo da camada.

## Solution

Um **plugin do QGIS** com um algoritmo do Processing, "Numeração de
trechologradouro por logradouro", que porta as regras da **numeração automática**
já especificadas em C# para Python e as roda sobre uma camada de linhas do
projeto:

- O operador escolhe a camada de trechos, o atributo do código do logradouro, o
  atributo (inteiro, já existente) onde gravar o **número sequencial do trecho**,
  e as duas tolerâncias (interseção de vértices, default 0,05 m; gap entre
  trechos, default 30 m).
- Sem o checkbox "apenas feições selecionadas", numera **todos os
  `COD_LOGRADOURO` distintos** da camada; com ele, só os códigos presentes entre
  os trechos selecionados.
- Não há modo por área/MBR — é sempre "por logradouro".
- Grava o inteiro incremental por segmento (o `1` de `01052.0001`, sem máscara)
  direto no atributo escolhido da própria camada.
- Um `COD_LOGRADOURO` que já tenha esse atributo preenchido em pelo menos um
  trecho é considerado já numerado e é ignorado.
- Um logradouro cuja topologia não fecha (vão acima da tolerância, beco sem
  saída) é pulado com aviso no log, e a execução segue. No fim, um resumo:
  quantos numerados, quantos ignorados por já estarem numerados, quantos
  falharam.

## User Stories

1. Como cadastrador, quero rodar a numeração dentro do QGIS sobre a camada que já
   está aberta, sem subir serviço nem depender do Oracle.
2. Como cadastrador, quero que o algoritmo apareça no Processing Toolbox, para
   usar como qualquer outra ferramenta do QGIS (inclusive em modelo e batch).
3. Como cadastrador, quero escolher a camada de trechos num seletor de camada de
   linha.
4. Como cadastrador, quero escolher o atributo do código do logradouro num
   seletor de campo da camada.
5. Como cadastrador, quero escolher o atributo onde o número sequencial será
   gravado num seletor de campo da camada.
6. Como cadastrador, quero que o algoritmo recuse um atributo de destino que não
   seja numérico (texto), com mensagem clara. Inteiro ou real servem — o valor
   gravado é sempre o inteiro (o `NUMBER` do Oracle chega ao QGIS como real).
7. Como cadastrador, quero informar a tolerância de interseção de vértices, com
   0,05 m já preenchido como padrão.
8. Como cadastrador, quero informar a tolerância de gap entre trechos do mesmo
   logradouro, com 30 m já preenchido como padrão.
9. Como cadastrador, quero, sem seleção ativa, numerar todos os `COD_LOGRADOURO`
   distintos da camada de uma vez.
10. Como cadastrador, quero, com trechos selecionados, numerar apenas os
    `COD_LOGRADOURO` presentes nessa seleção.
11. Como cadastrador, quero que o resultado seja gravado direto no atributo da
    camada de entrada, sem gerar camada nova.
12. Como cadastrador, quero que o valor gravado seja o inteiro incremental por
    segmento (1, 2, 3…), sem a máscara `NNNNN.NNNN`.
13. Como cadastrador, quero que o número comece em 1 para cada logradouro e
    incremente a cada cruzamento, repetindo entre trechos do mesmo segmento —
    exatamente como o `CODTRECHOLOGRADOURO` do serviço C#, só que sem a máscara.
14. Como cadastrador, quero que um `COD_LOGRADOURO` com o atributo de número
    sequencial já preenchido (não-NULL) em pelo menos um trecho seja ignorado,
    para não renumerar o que já foi feito.
15. Como cadastrador, quero ver no log quantos logradouros foram ignorados por já
    estarem numerados — e, quando isso significa que **nada** foi gravado (0 a
    numerar) ou que um logradouro que eu selecionei à mão foi descartado, quero
    um **aviso** explícito lembrando de "Sobrescrever numeração", não uma linha
    de info que passa batida.
15a. Como cadastrador, quero que trechos com `COD_LOGRADOURO` nulo sejam
    desconsiderados (fora de escopo, fora do grafo, não são cruzamento), com a
    contagem no log.
15b. Como cadastrador, quero que uma escrita recusada pelo QGIS vire erro (nada
    gravado pela metade), nunca um resumo dizendo "atualizado" sem ter gravado.
16. Como cadastrador, quero que a detecção de cruzamento considere trechos de
    **outros** `COD_LOGRADOURO` que tocam os nós, igual ao C# — mesmo numerando um
    logradouro só.
17. Como cadastrador, quero que a operação funcione com a camada de trechos
    inteira carregada no projeto; o filtro de vizinhança assume isso.
18. Como cadastrador, quero que a escolha do trecho inicial siga a regra do C#:
    entre as extremidades, ordenadas pela distância ao canto inferior esquerdo do
    MBR do logradouro, a primeira que consegue numerar tudo.
19. Como cadastrador, quero que a bifurcação de mesmo `COD_LOGRADOURO` siga a
    continuação mais reta e depois volte ao nó pendente mais recente (LIFO),
    igual ao C#.
20. Como cadastrador, quero que trechos disjuntos do mesmo logradouro sejam
    encadeados pela ponta mais próxima do último vértice numerado, respeitando a
    tolerância de gap, igual ao C#.
21. Como cadastrador, quero que um logradouro com vão acima da tolerância seja
    pulado, com um aviso no log dizendo o `COD_LOGRADOURO`, a distância e os
    `IDPKTRLOGR`/id das feições dos dois lados do vão.
22. Como cadastrador, quero que um logradouro que não fecha por qualquer outro
    motivo (beco sem saída no DFS) seja pulado com aviso, sem abortar a execução.
23. Como cadastrador, quero um resumo ao fim: quantos logradouros numerados,
    quantos ignorados por já numerados, quantos falharam.
24. Como cadastrador, quero que o algoritmo recuse uma camada em CRS geográfico
    (graus), com mensagem pedindo para reprojetar para um CRS métrico — as
    tolerâncias são em metros e o cálculo é planar, como no C#.
25. Como cadastrador, quero barra de progresso e cancelamento, aproveitando o
    feedback nativo do Processing.
26. Como mantenedor, quero o plugin numa pasta `plugin-qgis/` na raiz do repo,
    com o pacote instalável `numeracao_trechologradouro/` dentro dela.
27. Como mantenedor, quero `metadata.txt` com nome "Numeração de trechologradouro
    por logradouro", `qgisMinimumVersion=3.28`, `version=0.1.0`, autor
    "Prefeitura de Betim", email `tuffisal@gmail.com`.
28. Como mantenedor, quero que as primitivas geométricas usem recursos nativos do
    QGIS (`QgsPointXY.distance`, `QgsVector`, `QgsSpatialIndex`, iteração de
    vértices do `QgsGeometry`), não funções próprias.
29. Como mantenedor, quero que só o algoritmo de grafo/sequenciamento (regra de
    domínio) seja escrito à mão — nenhuma rotina que o QGIS já ofereça é
    reimplementada.
30. Como mantenedor, quero um ADR registrando por que o plugin porta o algoritmo
    para Python em vez de chamar o serviço C# a partir do QGIS.
31. Como mantenedor, quero que o código Python passe em `py_compile` e siga a
    estrutura padrão de plugin do QGIS (metadata, `__init__.py`, provider,
    algoritmo), para carregar sem erro no QGIS 3.28.
32. Como mantenedor do glossário, quero os termos **Número sequencial do trecho**
    e **Plugin do QGIS** no `CONTEXT.md` (já adicionados na modelagem) refletidos
    no spec.

## Implementation Decisions

### Estrutura do plugin

- `plugin-qgis/` na raiz do repo é o contêiner; dentro, o pacote instalável
  `numeracao_trechologradouro/` (nome válido como módulo Python).
- Pacote: `metadata.txt`, `__init__.py` (com `classFactory`), classe de plugin
  que registra um `QgsProcessingProvider`, e o `QgsProcessingAlgorithm`.
- `metadata.txt`: `name=Numeração de trechologradouro por logradouro`,
  `qgisMinimumVersion=3.28`, `version=0.1.0`, `author=Prefeitura de Betim`,
  `email=tuffisal@gmail.com`, `description`/`about` curtos, `hasProcessingProvider=yes`.

### Parâmetros do algoritmo

- Camada de entrada: `QgsProcessingParameterVectorLayer` restrita a geometria de
  linha (precisa ser uma camada gravável do projeto; `QgsProcessingParameterFeatureSource`
  com `parameterAsVectorLayer` devolve `None` quando a opção "apenas
  selecionadas" está marcada — por isso não é usado).
- "Numerar apenas os logradouros das feições selecionadas":
  `QgsProcessingParameterBoolean`, default **`True`** (o operador desmarca para
  processar a camada inteira — revisto a pedido do operador, era `False`).
  Quando ligado e sem seleção, erro claro.
- Atributo do código do logradouro: `QgsProcessingParameterField` (parentLayer =
  a camada), tipo qualquer.
- Atributo do número sequencial: `QgsProcessingParameterField` (parentLayer = a
  camada), validado em runtime como numérico (inteiro ou real); erro se for
  texto.
- Tolerância de interseção de vértices: `QgsProcessingParameterNumber` (Double),
  default `0.05`, mínimo 0.
- Tolerância de gap entre trechos: `QgsProcessingParameterNumber` (Double),
  default `30.0`, mínimo 0.
- Sem parâmetro de saída (grava na camada de entrada).

### Fluxo de execução

1. Valida CRS da camada como projetado (unidade metro); senão,
   `QgsProcessingException` com mensagem pedindo reprojeção.
2. Valida o campo de destino como numérico (inteiro ou real); senão,
   `QgsProcessingException`. O valor gravado é sempre `int`.
3. Lê **todas** as feições de linha da camada (a operação pressupõe a camada
   inteira carregada) para dentro de estruturas em memória: por feição, id, valor
   do campo de código, geometria; monta um `QgsSpatialIndex` das feições. Feição
   com o campo de código **nulo** é desconsiderada por completo (fora das
   estruturas e do índice — não entra em escopo nem vira cruzamento); o log
   avisa a contagem.
4. Determina os `COD_LOGRADOURO` em escopo: distintos de toda a camada, ou —
   com a opção "apenas selecionadas" ligada — os `COD_LOGRADOURO` das feições em
   `camada.selectedFeatureIds()`. A camada inteira continua acessível para o
   grafo.
5. Para cada `COD_LOGRADOURO` em escopo:
   a. Se qualquer trecho dele já tem o campo de número sequencial não-NULL →
      ignora, incrementa o contador "já numerados" (a menos que "Sobrescrever
      numeração" esteja ligado). Se ao fim **nenhum** logradouro sobra para
      numerar, ou se "apenas selecionadas" está ligado e algum código
      selecionado foi ignorado, o log recebe um **aviso** explícito (não só a
      linha de info) dizendo que nada foi gravado / quais foram descartados e
      lembrando de "Sobrescrever numeração".
   b. Monta (ou reaproveita) um **grafo compartilhado** cobrindo a vizinhança:
      todas as feições cujo retângulo envolvente intersecta o bbox dos trechos
      em escopo expandido pela tolerância de encaixe (consulta ao
      `QgsSpatialIndex`). Nós = pontas de trecho agrupadas pela tolerância de
      interseção de vértices; cruzamento = grau ≥ 3 **ou** mais de um
      `COD_LOGRADOURO` distinto incidente no nó.
   c. `DefinirAlvo` = os trechos do código atual; roda o sequenciador
      multi-candidato; roda a atribuição por segmento; escreve o inteiro em cada
      trecho.
   d. `NumberingException` equivalente (vão acima da tolerância, DFS sem
      fechamento) → pula, `feedback.pushWarning` com código + distância + ids,
      incrementa "falhados".
6. Aplica os valores na **edição** da camada: `startEditing()` se ainda não
   estiver editável, `beginEditCommand` / `changeAttributeValue` /
   `endEditCommand` (um único passo de desfazer), `triggerRepaint()`. **Não faz
   `commitChanges()`** — os valores ficam no buffer de edição (visíveis no mapa
   e na tabela) e só são persistidos quando o operador clica em "Salvar edições
   da camada"; "Reverter" desfaz tudo. Se a camada for de banco, nada vai ao
   banco até esse salvamento. O retorno de cada `changeAttributeValue` é
   checado: uma recusa vira `QgsProcessingException` dentro do comando de edição
   (comando destruído, nada gravado pela metade).
7. `feedback` recebe o resumo: numerados, já numerados (ignorados), falhados,
   mais uma linha lembrando de salvar/reverter as edições.

### Porte das regras (fiel ao C#)

- **Parser de geometria**: itera os vértices do `QgsGeometry` (achata
  multipartes), primeiro = início, último = fim — no lugar do `WKTReader`.
- **Grafo**: mesma semântica do `GrafoLogradouro` já generalizado — índice de nós
  compartilhado + conjunto de códigos por nó (construtor), arestas/grau/
  cruzamento por alvo (`DefinirAlvo`). Agrupamento de nó usa `QgsSpatialIndex`
  para achar o nó existente dentro da tolerância, em vez de varredura linear.
- **Sequenciador**: porte de `SequenciadorAutomatico` — candidatos de partida =
  extremidades ordenadas pela distância (via `QgsPointXY.distance`) ao canto
  inferior esquerdo do MBR do alvo; tenta cada candidato até um numerar todos os
  trechos; DFS com continuação mais reta usando `QgsVector.normalized()` +
  `QgsVector.dotProduct()`; pilha LIFO de bifurcações; `ContinuarDisjunto` com a
  tolerância de gap; mensagem de falha com os dois ids.
- **Atribuição**: porte de `AtribuidorDeCodigos` — percorre a ordem, `+1` quando
  não há nó compartilhado ou o nó compartilhado é cruzamento, herda caso
  contrário, começa em 1. **Sem** as validações de `99999`/`9999` (eram limites
  da máscara). Grava `n` inteiro.

### Documentação

- Novo ADR: porte paralelo do algoritmo para Python no plugin, em vez de o QGIS
  consumir o serviço C# — trade-off entre duplicação (duas implementações da
  mesma regra a manter em sincronia) e a alternativa (UX nativa do Processing,
  operação offline, sem dependência de servidor/Oracle).
- `CONTEXT.md`: termos **Número sequencial do trecho** e **Plugin do QGIS** já
  adicionados na modelagem.

## Testing Decisions

- **Sem suíte automatizada dentro do repo** para o plugin nesta rodada —
  consistente com as rodadas anteriores (verificação manual). O núcleo do
  algoritmo depende de tipos do `qgis.core` (`QgsVector`, `QgsSpatialIndex`,
  `QgsGeometry`), então não roda fora do QGIS; um harness puro-Python exigiria
  não usar os nativos, o que contraria a regra 2.
- **Seam de verificação — sintaxe e estrutura**: `python -m py_compile` em todos
  os `.py` do plugin; a estrutura de plugin (metadata, `classFactory`, provider,
  algoritmo com `initAlgorithm`/`processAlgorithm`) confere com o esperado pelo
  QGIS 3.28.
- **Seam de verificação — comportamento**: o operador carrega o plugin no QGIS
  3.28, roda o algoritmo na camada real de trechos e confere o número sequencial
  gravado contra o serviço C# para códigos conhecidos: `COD_LOGRADOURO` 1052 →
  segmentos 1 e 2; `COD_LOGRADOURO` 1171 → o encadeamento dos dois componentes
  disjuntos com o vão de ~26 m fechado (mesmo resultado da correção C# do
  sequenciador multi-candidato).
- Prior art: verificação por comparação direta com o serviço C# contra dados
  reais, como já feito nesta sessão para o `numeracao-em-lote`.

## Out of Scope

- Máscara `NNNNN.NNNN` — será tratada numa consulta futura, não aqui.
- Modo por área/MBR no plugin.
- Reprojeção interna de camada em CRS geográfico (só recusa com mensagem).
- Gerar camada de saída nova (grava sempre na camada de entrada).
- Parâmetro de "atributo de id do trecho" para desempate — usa o id da feição.
- Preencher só valores nulos / renumerar logradouros já numerados.
- Empacotamento como `.zip` publicável / repositório de plugins do QGIS.
- Testes automatizados no repositório para o plugin.
- Qualquer mudança no serviço C#, na API ou no front-end.

## Further Notes

- O QGIS MCP não estava conectado durante a modelagem; a versão mínima 3.28 foi
  definida pelo operador.
- O algoritmo pode rodar sobre milhares de trechos (camada inteira ~16 mil no
  dado real). O agrupamento de nós tem que usar o `QgsSpatialIndex` para não cair
  em O(n²); o mesmo índice serve para o filtro de vizinhança do grafo.
- A regra "ignora logradouro já numerado" olha o campo por trecho antes de
  qualquer trabalho — barato, evita montar grafo para o que não vai ser numerado.
- A gravação na camada é a única parte destrutiva; deve estar sob controle de
  edição do QGIS (transação/undo) para o operador poder desfazer.
