# `CODTRECHOLOGRADOURO` identifica um segmento, não um trecho

Antes, a numeração dava um incremental novo a cada trecho, então
`CODTRECHOLOGRADOURO` era único por `IDPKTRLOGR`. Passamos a atribuir o **mesmo**
código a trechos contíguos do mesmo logradouro que se ligam apenas por **nós de
passagem** (grau 2, sem outra via); o incremental só avança num **cruzamento**
(nó tocado por outro `COD_LOGRADOURO` ou onde a via bifurca) ou num salto na
sequência. O código passa a identificar o **segmento** de via entre dois
cruzamentos.

## Motivação

A camada `TRECHOLOGRADOURO` de Betim é super-segmentada: uma mesma quadra de rua
costuma vir quebrada em 2+ trechos sem nenhum cruzamento entre eles. O usuário
quer que o `CODTRECHOLOGRADOURO` reflita o trecho de rua entre esquinas, não a
segmentação de cadastro.

## Consequências

- O corpo da API (`{ items: [{ IDPKTRLOGR, CODTRECHOLOGRADOURO }] }`) continua com
  **um item por trecho**, mas `CODTRECHOLOGRADOURO` **repete** entre itens do
  mesmo segmento. Qualquer consumidor precisa tratar o código como não-único na
  lista.
- A detecção de cruzamento exige conhecer **toda** a camada (as outras vias), não
  só o logradouro selecionado. O app mantém um índice global de nós construído
  uma vez na carga; o motor de numeração continua puro, recebendo o conjunto de
  nós-cruzamento já resolvido.
- `SOURCE`, `TARGET` e `NUM_SEQLOGRADOURO` continuam ignorados — cruzamento e
  contiguidade vêm só da geometria.
