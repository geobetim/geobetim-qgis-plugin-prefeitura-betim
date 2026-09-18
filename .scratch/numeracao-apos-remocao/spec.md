# Spec: Numerar após quebrar e remover trechos de passagem

**Status:** implementado

Opção nova no algoritmo "Quebrar e remover trechos de passagem"
(`.scratch/cruzamento-fora-de-escopo/`) para encadear a numeração automática
logo depois, sem precisar de uma segunda execução manual do Processing.

## Problem Statement

Depois de rodar a remoção/quebra, a geometria dos trechos muda (colapso de
segmento de passagem, quebra por cruzamento ou por camada de quebra) e a
numeração anterior fica obsoleta — o cadastrador precisa lembrar de rodar a
numeração automática de novo, manualmente, com "Sobrescrever numeração"
ligado, escolhendo de novo o mesmo escopo. É um passo repetitivo e fácil de
esquecer (o número antigo continua gravado, sem aviso de que a geometria
mudou por baixo dele).

## Solution

Um parâmetro booleano novo no algoritmo de remoção/quebra, desmarcado por
padrão: "Numerar os trechos após a remoção". Quando marcado, depois de
aplicar a remoção/quebra no escopo escolhido (selecionadas ou camada
inteira, conforme a opção já existente), o algoritmo numera automaticamente
os mesmos `COD_LOGRADOURO` afetados, sempre sobrescrevendo a numeração
anterior (já que a geometria acabou de mudar) — sem expor essa escolha como
parâmetro. Os parâmetros que os dois algoritmos compartilham (atributo de
agrupamento, "apenas selecionadas", tolerância de encaixe de vértices)
aparecem uma vez só na interface; os específicos da numeração (atributo do
número sequencial, tolerância de gap) aparecem separados, e só importam
quando a opção de encadear está marcada.

## User Stories

1. Como cadastrador, quero marcar "Numerar os trechos após a remoção" e ver,
   numa única execução, os trechos removidos/quebrados e depois numerados,
   sem precisar abrir o algoritmo de numeração de novo.
2. Como cadastrador, quero que essa opção venha **desmarcada por padrão**,
   para que quem só quer remover/quebrar continue com o comportamento de
   hoje, sem numeração nenhuma.
3. Como cadastrador, quero que o atributo de agrupamento (código do
   logradouro), a opção "apenas selecionadas" e a tolerância de encaixe de
   vértices apareçam **uma vez só** na tela do algoritmo — não duplicados
   entre a parte de remoção e a parte de numeração.
4. Como cadastrador, quero que o atributo do número sequencial e a
   tolerância de gap apareçam num grupo separado dos parâmetros de
   remoção/quebra, para que fique claro que são específicos da numeração.
5. Como cadastrador, quero que, quando eu marco a numeração encadeada, ela
   sempre sobrescreva a numeração anterior — sem ter que marcar isso
   também, e sem que essa escolha apareça como um parâmetro na tela.
6. Como cadastrador, quero que o algoritmo de numeração standalone continue
   com "Sobrescrever numeração" desmarcado por padrão, do jeito que já é —
   essa mudança só vale dentro do fluxo encadeado.
7. Como cadastrador, quero que a numeração encadeada rode só nos
   `COD_LOGRADOURO` que a remoção/quebra efetivamente processou naquela
   execução (o escopo escolhido — selecionados ou toda a camada), não em
   nenhum código extra.
8. Como cadastrador, quero que, se a numeração falhar para um
   `COD_LOGRADOURO` (ex.: gap maior que a tolerância) depois que a
   remoção/quebra já rodou com sucesso para ele, a remoção/quebra continue
   valendo — nada é desfeito automaticamente — e o log me avise qual código
   falhou na numeração e por quê.
9. Como cadastrador, quero poder desfazer tudo (remoção/quebra e numeração)
   de uma vez, pelo botão "Reverter edições da camada" do QGIS, já que
   nada é gravado em definitivo até eu salvar — sem precisar de um botão de
   reversão específico do plugin.
10. Como cadastrador, quero que o resumo final do algoritmo relate os dois
    resultados (quantos trechos removidos/quebrados, quantos logradouros
    numerados/ignorados/com falha), para ter uma visão completa sem abrir o
    log em duas partes.
11. Como desenvolvedor mantendo o plugin, quero que a numeração encadeada
    reaproveite as mesmas funções puras que `numeracao_trecho_logradouro`
    já usa (`GrafoLogradouro`, `SequenciadorAutomatico`, `atribuir`), lendo
    a camada de novo depois da remoção/quebra (para ver a geometria já
    atualizada no buffer de edição), sem instanciar o
    `QgsProcessingAlgorithm` da numeração como sub-algoritmo.
12. Como cadastrador, quero que a tolerância de encaixe de vértices
    compartilhada valha tanto para a detecção de cruzamento da
    remoção/quebra quanto para a montagem do grafo da numeração encadeada —
    um valor só, sem risco de configurar tolerâncias diferentes por
    engano.

## Implementation Decisions

- Novo `QgsProcessingParameterBoolean` no algoritmo de remoção/quebra:
  `NUMERAR_APOS`, `defaultValue=False`, agrupado visualmente com os outros
  parâmetros de numeração (QGIS Processing não tem "grupos" nativos de
  parâmetros na maioria das versões-alvo; usar prefixo consistente no rótulo,
  ex.: "Numeração — ...", e ordem de declaração, para aproximar o efeito).
- Parâmetros específicos da numeração (`CAMPO_SEQUENCIAL`, `TOL_GAP`) só
  fazem sentido quando `NUMERAR_APOS` está marcado — continuam existindo
  como parâmetros normais (QGIS Processing não esconde parâmetros
  condicionalmente de forma simples entre versões); o `shortHelpString`
  deixa explícito que são ignorados se a opção não estiver marcada.
- `CAMPO_CODIGO` (atributo de agrupamento), `APENAS_SELECIONADAS` e
  `TOL_VERTICE` (tolerância de encaixe) continuam sendo os únicos parâmetros
  desses conceitos — a numeração encadeada os reaproveita diretamente, sem
  pedir de novo.
- **Não existe** um parâmetro de "sobrescrever numeração" na tela do
  algoritmo de remoção/quebra — quando `NUMERAR_APOS` está marcado, o valor
  é sempre `True` internamente, na chamada às funções de numeração.
- Sequência de execução dentro de `processAlgorithm` da remoção/quebra:
  fase 0, fase 1, fase 2, aplica tudo na edição da camada (como hoje) e só
  **depois** — com o bloco de edição da remoção/quebra já fechado, para que
  a numeração leia a geometria atualizada do buffer — lê a camada de novo
  (`ler_camada`), monta `GrafoLogradouro` sobre a vizinhança dos códigos
  processados, numera cada um com `SequenciadorAutomatico`/`atribuir`, e
  aplica os números num segundo bloco de edição (mesma camada, sem commit).
  Uma falha de numeração num código específico gera aviso e não interrompe
  os demais — mesmo padrão que a numeração standalone já usa.
- O escopo numerado é exatamente `codigos_escopo` da remoção/quebra (os
  mesmos códigos processados nas fases 1/2) — nunca inclui um código de fora
  dividido pela opção "Também quebrar o outro logradouro no cruzamento"
  (`.scratch/cruzamento-fora-de-escopo/`), que fica restrito ao corte, sem
  entrar em nenhuma fase adicional, incluindo a numeração encadeada.
- Mensagem final do algoritmo passa a reportar as duas contagens (removidos
  /quebrados; numerados/ignorados/com falha) quando `NUMERAR_APOS` está
  marcado; sem a opção, o resumo continua igual a hoje.

## Testing Decisions

- Mesmo padrão de stub de `qgis.core` com geometria real.
- Teste de integração no nível do `algoritmo.py` da remoção/quebra (a seam
  já usada nos testes ponta a ponta do `7640`): com `NUMERAR_APOS` marcado,
  depois de colapsar/quebrar um `COD_LOGRADOURO` sintético com múltiplos
  trechos, os números sequenciais aplicados devem refletir a geometria
  **pós**-remoção, não a original — prova de que a numeração lê o estado
  atualizado do buffer, não a leitura original da camada.
- Caso de falha controlada: um `COD_LOGRADOURO` cuja numeração falha (gap
  maior que a tolerância) depois de uma remoção/quebra bem-sucedida — a
  remoção/quebra permanece aplicada (não é desfeita), e o aviso de falha da
  numeração aparece no log.
- Caso de controle: `NUMERAR_APOS` desmarcado — resultado idêntico ao
  algoritmo antes desta mudança (nenhum número sequencial tocado).
- Regressão: a numeração standalone (`numeracao_trecho_logradouro`)
  continua com seus próprios testes existentes intactos — este spec não
  modifica esse módulo, só o consome.

## Out of Scope

- Qualquer interface gráfica além dos parâmetros padrão do Processing (sem
  diálogo customizado, sem abas).
- Desfazer automaticamente a remoção/quebra se a numeração falhar — decisão
  já tomada: reversão é manual, pelo botão "Reverter" do QGIS.
- Mudar o comportamento ou os parâmetros do algoritmo de numeração
  standalone.
- Encadear no sentido contrário (numerar e depois remover/quebrar) — fora de
  escopo, não foi pedido.

## Further Notes

- Combinado com `.scratch/cruzamento-fora-de-escopo/` (a opção "Também
  quebrar o outro logradouro no cruzamento"), este encadeamento resolve o
  caso real que motivou os dois specs: rodar "Quebrar e remover trechos de
  passagem" no `7643`, com as duas opções marcadas, quebra `33748` (do
  `7647`) no cruzamento e já numera `7643` corretamente na mesma execução,
  sem passo manual entre os dois.
