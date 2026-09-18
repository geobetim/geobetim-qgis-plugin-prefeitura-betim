# A própria camada de trechos é fonte obrigatória de cruzamento

A **remoção de trecho de passagem** ganha uma fase 0, antes do colapso: a
**camada de trechos** — não uma **camada de quebra** auxiliar, sempre opcional
— passa a ser usada, **sempre**, para achar cruzamento entre `COD_LOGRADOURO`
diferentes. Onde um trecho em escopo cruza — com ou sem nó compartilhado hoje,
inclusive um X sem vértice em nenhum dos dois lados — um trecho de **outro**
`COD_LOGRADOURO` na mesma camada, ele é dividido ali; o outro `COD_LOGRADOURO`
nunca é tocado, mesmo fora de escopo.

## Motivação

A identificação de **cruzamento** sempre pressupôs que os dois lados já têm um
**nó** (uma ponta de trecho) no mesmo lugar. Isso falha quando um logradouro
foi digitalizado sem dividir o trecho onde ele cruza outro — o caso real que
motivou este ADR: `COD_LOGRADOURO 7647` é um único trecho (`IDPKTRLOGR 33748`)
que atravessa `COD_LOGRADOURO 7643` por dentro do próprio traçado, sem nó em
nenhum dos dois lados (o vértice mais próximo de `33748` fica a ~2,8 mm do nó
real de `7643`, dentro da tolerância de 0,05 m — não é um problema de dado
degenerado, é falta de divisão). Sem essa fase, a remoção de trecho de
passagem não tem como enxergar esse cruzamento: não há segmento de passagem
para colapsar (um trecho só não forma segmento), e a quebra existente só age
contra **camadas de quebra** auxiliares e opcionais — nunca contra a própria
camada de trechos.

## Escolha

- A camada de trechos é fonte de cruzamento **sempre**, sem parâmetro para
  ligar/desligar — diferente das camadas de quebra, que continuam auxiliares
  e opcionais (até duas).
- Roda como **fase 0**, antes da identificação de segmentos de passagem (fase
  1): a topologia que a fase 1 enxerga já reflete os cortes da fase 0.
- Detecta e corta contra a topologia **original** (o que a leitura da camada
  trouxe), nunca o resultado já cortado de outro trecho do mesmo laço — o
  resultado não depende da ordem em que os trechos em escopo são visitados.
- O nó de cada corte é marcado **cruzamento** explicitamente (no mesmo
  conjunto que já bloqueia nó de passagem por camada de quebra) — não depende
  de o outro `COD_LOGRADOURO` ter, ele também, um nó real ali. Sem essa marca,
  um cruzamento em X puro (nenhum vértice em nenhum lado antes do corte)
  ficaria com um nó "só do lado dele", identificável como nó de passagem
  comum, e o corte seria desfeito no primeiro colapso.
- Cruzamento entre trechos do **mesmo** `COD_LOGRADOURO` sem nó compartilhado é
  atípico (dado mal digitalizado) e **não** é dividido — só gera aviso no log,
  para o cadastrador investigar.
- A chave primária de um pedaço criado pela fase 0 é resolvida **na hora**
  (decisão do operador — ver ADR-0005), não adiada para depois do colapso: mais
  simples de implementar, e o valor real já entra no desempate do absorvedor
  em vez de um id temporário; o custo é aceitar o mesmo risco de buraco na
  sequência se a fase 1 vier a apagar o pedaço depois.
- Um pedaço da fase 0 ainda não é uma feição de verdade: circula pelas
  estruturas em memória por um identificador temporário (nunca um id real de
  feição do QGIS) até a aplicação final da edição — só nesse ponto se torna
  `QgsFeature`, junto com os registros novos da quebra por camada de quebra
  (fase 2), preservando a atomicidade já estabelecida (tudo calculado em
  memória antes de qualquer escrita na camada).
- ADR-0004 (porte para Python) e ADR-0005 (`IDPKTRLOGR` via `GFIELDMAPPING`)
  permanecem válidos; este ADR reaproveita a mesma resolução de chave, não a
  altera.

## Consequências

- Custo de comparar cada trecho em escopo contra a vizinhança de outros
  códigos — mitigado reaproveitando os dados já carregados em memória para a
  fase 1 (sem nova consulta à camada) e um índice espacial próprio sobre essa
  vizinhança, em vez de comparação em pares sem filtro.
- Complexidade do identificador temporário: um id que nunca existiu na camada
  precisa participar da identificação de segmento e do colapso como qualquer
  outro trecho, e, se absorvido, ser descartado sem nunca chamar
  `deleteFeature` nele. Mitigação: o identificador é opaco para quem chama —
  o módulo que o cria também devolve a informação de qual id real é a sua
  origem, para copiar atributos e resolver a chave.
- Um id **real** que a fase 0 truncou precisa ir para a edição com a geometria
  truncada mesmo que nem a fase 1 nem a fase 2 o toquem de novo depois — senão
  a camada ficaria com a geometria original inteira, duplicando o traçado que
  o pedaço novo passou a cobrir.
- Sem suíte de testes no repositório que rode dentro do QGIS de verdade —
  verificação por stub de `qgis.core` (geometria real: interseção, distância ao
  longo da linha, corte de curva) cobrindo o cruzamento real do `7647`/`7643`,
  casos sintéticos (X puro, múltiplas interseções, mesmo código atípico) e o
  algoritmo completo ponta a ponta; e o operador rodando no QGIS 3.28 sobre a
  camada real.
