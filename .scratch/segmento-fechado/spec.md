# Spec: Colapso de segmento de passagem fechado (anel)

**Status:** implementado (ticket 01); verificação do operador no QGIS 3.28
pendente.

Revisão pontual da spec `.scratch/remover-trechos-passagem/spec.md` (fase 1 —
colapso). Motivada pelo `COD_LOGRADOURO 7542`, que hoje termina em
"segmento fechado [...] não encadeia; não colapsado".

## Problem Statement

Um logradouro em forma de "balão" — trechos ligados só por **nós de passagem**
que dão a volta e se fecham num único nó — é um **segmento de passagem** como
qualquer outro e deveria colapsar num trecho só. Hoje a **remoção de trecho de
passagem** identifica o segmento corretamente, mas a emenda das geometrias
falha em metade dos casos e o logradouro é pulado com aviso. A falha não tem a
ver com o dado: no 7542 todos os nós compartilhados coincidem exatamente. Ela
depende só de a geometria do **trecho absorvedor** estar, no banco, orientada no
mesmo sentido em que a lista do segmento foi girada — moeda ao ar.

Há ainda um problema de coerência: quando a emenda funciona, o anel resultante
começa/termina num nó qualquer do antigo segmento (o da ponta do absorvedor),
não no nó que fechava o segmento. Se esse nó de fechamento era um
**cruzamento** (no 7542, o nó onde encosta o toco `29810`, do mesmo código), ele
vira um vértice interno do anel — deixa de ser nó — e o trecho que encostava ali
fica solto: para a **numeração automática**, passa a ser **trecho desconectado**
alcançado só pelo gap.

## Solution

- O colapso de um segmento fechado sempre funciona quando as geometrias de fato
  se encadeiam: o primeiro trecho da emenda é orientado pelo nó de fechamento,
  e cada trecho seguinte pela ponta comum com o anterior (como já é).
- O trecho fechado resultante **começa e termina no nó de fechamento** do
  segmento — o nó compartilhado pela primeira e pela última ponta do segmento.
  Quando esse nó é cruzamento (balão pendurado numa via, toco encostado), a
  topologia fica coerente: quem encostava ali continua encostando numa ponta do
  trecho. Num anel isolado, sem cruzamento nenhum, qualquer nó do anel serve
  como fechamento — o algoritmo usa o nó que já era a ponta do segmento.
- Nada muda para segmentos abertos (caminhos): a absorção a partir do
  absorvedor para os dois lados continua igual.

## User Stories

1. Como cadastrador, quero que um logradouro em forma de balão (anel de nós de
   passagem preso a um cruzamento) colapse num trecho só, para não ter que
   emendar cinco trechos na mão.
2. Como cadastrador, quero que o resultado do colapso de um anel não dependa da
   orientação em que a geometria do absorvedor foi digitalizada, para o
   algoritmo ser determinístico e não "funcionar às vezes".
3. Como cadastrador, quero que o trecho fechado comece e termine no nó que
   fechava o segmento, para um trecho que encostava nesse nó (como o toco
   `29810`) continuar encostando numa ponta do trecho, não no meio dele.
4. Como cadastrador, quero que um anel isolado (sem nenhum cruzamento) também
   colapse num trecho fechado, começando e terminando num dos nós antigos do
   anel.
5. Como cadastrador, quero que o trecho fechado tenha todos os vértices dos
   trechos do segmento, na ordem do anel, sem duplicar os nós compartilhados —
   igual ao que já vale para segmentos abertos.
6. Como cadastrador, quero que o **trecho absorvedor** de um anel continue sendo
   o maior por comprimento (empate → menor chave primária configurada), o
   único registro que sobrevive — mesmo que o anel comece/termine longe da
   ponta original dele.
7. Como cadastrador, quero que, quando um anel de fato não encadeia (geometria
   inconsistente, trecho com menos de 2 vértices), o logradouro continue sendo
   pulado com o aviso atual — o aviso passa a significar dado ruim, não azar.
8. Como cadastrador da numeração, quero que, depois do colapso do balão e da
   renumeração com "Sobrescrever numeração", o toco e o anel do 7542 sejam
   tratados como conectados pelo nó de fechamento, não pelo gap.
9. Como mantenedor, quero o comportamento de segmento aberto intocado —
   nenhuma mudança nas mensagens, contagens ou geometrias fora do caso de anel.
10. Como mantenedor do glossário, quero o **trecho absorvedor** de um segmento
    fechado descrito no `CONTEXT.md` (anel começa/termina no nó de fechamento)
    — já feito na modelagem.

## Implementation Decisions

- Só a fase 1 (colapso) do algoritmo de remoção muda, e só o ramo de segmento
  fechado. Identificação de segmentos, fase 2 (quebra), chave primária, resumo
  e aplicação na edição ficam como estão.
- **Detecção do anel**: mantida — segmento com 3+ trechos cujo primeiro e último
  trecho compartilham um nó. Esse nó compartilhado é o **nó de fechamento**.
- **Encadeamento do anel**: a emenda parte do primeiro trecho da ordem do
  segmento (o que toca o nó de fechamento), orientado para **começar** no nó de
  fechamento, e segue a ordem até o último trecho, que termina de volta nesse
  nó. A novidade é orientar o **primeiro** trecho pelo nó de fechamento em vez
  de usar a geometria como está no banco; os seguintes já são orientados pela
  ponta comum. Deixa de existir a rotação da lista para começar no absorvedor.
- **Absorvedor**: escolhido como hoje (maior comprimento; empate → menor chave
  configurada / id). Recebe a polilinha fechada completa; os demais trechos do
  segmento são apagados. O absorvedor não precisa ser o primeiro da emenda —
  ele é só o registro que sobrevive.
- **Anel isolado** (todos os nós de passagem, sem cruzamento): a ordem do
  segmento já começa no menor id, e o nó compartilhado entre o primeiro e o
  último trecho é o nó de fechamento por definição. Mesma regra, sem caso
  especial.
- **Falha real de emenda** (ponta seguinte não toca a ponta corrente dentro da
  tolerância, ou trecho com < 2 vértices): mantém o aviso "segmento fechado
  [...] não encadeia; não colapsado" e pula o logradouro.
- `CONTEXT.md`: **Trecho absorvedor** com a frase sobre o segmento fechado (já
  aplicado). Sem ADR — acabamento de regra existente, reversível, sem
  trade-off arquitetural.

## Testing Decisions

- **Seam**: a função de colapso da remoção — recebe os segmentos ordenados, o
  índice de nós, as coordenadas e geometrias por trecho e a tolerância, e
  devolve geometria nova por absorvedor, ids a apagar e avisos. É o seam já
  usado nos tickets 03/06/08 com stub de `qgis.core` — nenhum seam novo.
- Um bom teste olha só o que sai: qual id sobreviveu, quais ids são apagados,
  quantos vértices tem a polilinha, onde ela começa/termina, se fecha. Não olha
  a ordem interna de emenda.
- **Casos**, com stub de `qgis.core` (`QgsPointXY`, `QgsSpatialIndex`,
  `QgsRectangle`), coordenadas reais do WFS para o primeiro:
  1. `COD_LOGRADOURO 7542` (balão): 1 absorvedor (`29807`), 4 apagados
     (`29806, 29808, 29809, 29811`), 318 vértices (soma dos 5 trechos menos os
     4 nós repetidos), primeiro = último vértice = nó de fechamento
     (`≈ 588821.85, 7795236.02`), zero avisos. Repetir com a geometria do
     absorvedor **invertida** e com a ordem do anel espelhada — mesmo resultado.
  2. Anel isolado de 4 trechos sintéticos: colapsa, fecha, começa/termina num
     nó do anel, zero avisos.
  3. Anel com um trecho de 1 vértice: pulado com o aviso atual, nada colapsado.
  4. Regressão de segmento aberto (`A—B—C—D`): resultado idêntico ao do ticket
     06.
- Prior art: os testes funcionais com stub de `qgis.core` desta base (tickets
  06–09) e a verificação com dado real do GeoServer (WFS
  `betimtaurus:TRECHOLOGRADOURO`) usada nos tickets 06 e 07.
- Verificação do operador no QGIS 3.28: rodar a remoção no 7542 → 1 trecho
  fechado + o toco `29810` encostado numa ponta; "Reverter" desfaz.

## Out of Scope

- Qualquer mudança em segmentos abertos, na identificação de segmentos, na
  fase 2 (quebra) ou na resolução de chave primária.
- Decidir o que fazer com o toco `29810` (0,3 m) — é dado; a remoção não apaga
  trecho que não seja de passagem.
- Anel com **mais de um** cruzamento — nesse caso não é um segmento fechado
  (são dois ou mais segmentos abertos), já coberto pelo modelo atual.
- Testes automatizados no repositório; mudanças no C#, na API ou no front-end.

## Further Notes

- Diagnóstico feito com as coordenadas reais do 7542 (WFS): nós compartilhados
  a distância 0; a falha foi reproduzida com o código atual e a correção de
  orientação foi validada no stub (318 vértices, anel fechado) antes de
  escrever este spec.
- A regra "anel começa/termina no nó de fechamento" é a única decisão nova de
  domínio aqui; o resto é correção de defeito.
