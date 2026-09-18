# Spec: Trecho degenerado — numeração e remoção

**Status:** implementado

## Problem Statement

A numeração automática de alguns `COD_LOGRADOURO` falha com um erro de "gap
acima da tolerância de continuação", mesmo quando os trechos do logradouro
estão, na realidade, bem conectados (as distâncias reais entre os pedaços
desconexos ficam bem dentro da tolerância padrão de 30 m). A causa é um
**trecho degenerado** — um trecho cujas duas pontas caem no mesmo nó, dentro
da tolerância de encaixe (ex.: `IDPKTRLOGR 33792`, no `COD_LOGRADOURO 7644`,
com 0,028 m de comprimento). Esse trecho cria um self-loop no grafo do
logradouro: o `SequenciadorAutomatico` só o consome por retrocesso (LIFO),
depois de já ter percorrido o resto do componente — e é nesse retrocesso que
a posição de referência para o salto entre componentes desconexos volta para
esse nó interior, em vez de ficar na extremidade real onde o percurso já
tinha chegado, inflando artificialmente a distância do salto calculado.

Uma checagem em toda a camada `TRECHOLOGRADOURO` (17.006 trechos, dados
reais do owner TUFFI) encontrou 10 trechos degenerados distintos, em 10
`COD_LOGRADOURO` diferentes; rodando a numeração real sobre eles, 4 falham
com esse padrão (`57`, `1078`, `7644`, `8130`) e 6 passam ilesos — depende de
onde o self-loop cai na ordem de percurso. Não é um caso isolado.

A mesma causa raiz (contagem de grau inflada pelo self-loop) também afeta a
**remoção de trecho de passagem**, com o efeito inverso: em vez de travar um
percurso, ela impede que o nó seja reconhecido como **nó de passagem** — o
trecho degenerado nunca entra em nenhum **segmento de passagem** e sobrevive
à operação sem ser tocado, mesmo quando os dois vizinhos reais deveriam
colapsar através dele.

## Solution

Formaliza **trecho degenerado** como conceito de domínio (já registrado em
`CONTEXT.md` e no `ADR-0008`) e corrige os dois algoritmos para tratá-lo como
se estivesse sempre num **nó de passagem**:

- Na **numeração automática**: o trecho degenerado nunca entra como
  candidato de percurso nem disputa bifurcação — é resolvido no momento em
  que seu nó é alcançado, herdando o **número sequencial do trecho** dos
  vizinhos reais, sem nunca mover a posição de referência do percurso
  (`_no_atual`). Isso corrige o cálculo do salto entre componentes
  desconexos sem alterar a semântica documentada da **tolerância de
  continuação**.
- Na **remoção de trecho de passagem**: a contagem de grau de um nó para de
  incluir as pontas do próprio trecho degenerado, permitindo que os dois
  vizinhos reais voltem a formar segmento de passagem entre si normalmente;
  o trecho degenerado é inserido na posição correta da lista ordenada desse
  segmento para ser absorvido pelo `colapsar` já existente — nunca é
  escolhido **trecho absorvedor**, por ser sempre o menor.
- **Escopo deliberado**: um trecho degenerado só é removido/renumerado
  quando seu nó corresponde a um nó de passagem real entre dois trechos do
  mesmo logradouro. Fora desse contexto (isolado, num cruzamento, ou numa
  extremidade) nenhum dos dois algoritmos o toca — só emite aviso, como
  problema de qualidade de dado para o operador investigar na origem.
- Os dois algoritmos emitem um aviso no feedback quando encontram um trecho
  degenerado, citando `IDPKTRLOGR` e `COD_LOGRADOURO`, esteja ele dentro ou
  fora do contexto de nó de passagem.

## User Stories

1. Como operador, quero que a numeração automática do `COD_LOGRADOURO 7644`
   (e dos demais códigos afetados pelo mesmo padrão) complete com sucesso,
   sem erro de gap, mesmo havendo um trecho degenerado no meio do traçado.
2. Como operador, quero que um trecho degenerado situado entre dois trechos
   reais do mesmo logradouro receba o mesmo número sequencial desses
   vizinhos, sem consumir uma posição nova na sequência.
3. Como operador, quero ser avisado (no log do algoritmo) sempre que a
   numeração automática encontrar um trecho degenerado, citando o
   `IDPKTRLOGR` e o `COD_LOGRADOURO`, para eu saber que existe um problema de
   qualidade de dado na origem.
4. Como operador, quero que a numeração automática de um logradouro sem
   nenhum trecho degenerado continue funcionando exatamente como antes —
   sem nenhuma mudança de comportamento ou de números atribuídos.
5. Como operador, quero que a remoção de trecho de passagem realmente apague
   um trecho degenerado que esteja no meio de um segmento de passagem,
   estendendo o trecho absorvedor através do ponto onde ele estava, sem
   deixar esse trecho de ~0 m sobrando na camada.
6. Como operador, quero ser avisado (no log do algoritmo) sempre que a
   remoção de trecho de passagem encontrar um trecho degenerado, citando o
   `IDPKTRLOGR` e o `COD_LOGRADOURO`.
7. Como operador, quero que um trecho degenerado isolado — sem nenhum
   vizinho real do mesmo `COD_LOGRADOURO` por perto — não seja tocado por
   nenhum dos dois algoritmos, e que eu receba um aviso claro em vez de um
   erro ou de uma remoção silenciosa incorreta.
8. Como operador, quero que um trecho degenerado situado exatamente num nó
   que já é um cruzamento real (bifurcação de 3 ou mais trechos, ou nó
   tocado por outro `COD_LOGRADOURO`) não seja removido nem renumerado como
   se fosse um trecho comum — só avisado — porque ali ele não está dentro de
   um segmento de passagem.
9. Como operador, quero que a remoção de trecho de passagem de um
   logradouro sem nenhum trecho degenerado continue funcionando exatamente
   como antes.
10. Como mantenedor, quero que a correção da numeração automática não altere
    a forma como a **tolerância de continuação** é calculada para trechos
    desconectados legítimos (eixo paralelo, pista dupla) — o bug e a
    correção são inteiramente sobre o tratamento do self-loop, não sobre a
    lógica de salto em si.
11. Como mantenedor, quero que a correção da remoção de trecho de passagem
    reaproveite o `colapsar`/`absorcao.py` já existente sem alterações —
    ele já lida corretamente com um trecho cujas duas pontas caem no mesmo
    ponto do trecho absorvedor (a extensão não adiciona vértice duplicado).
12. Como mantenedor, quero verificar a correção contra os quatro
    `COD_LOGRADOURO` reais que hoje falham (`57`, `1078`, `7644`, `8130`) e
    contra os seis que já passam, para confirmar que nenhum regride.

## Implementation Decisions

- **Numeração automática — grafo**: ao montar as arestas de um
  `COD_LOGRADOURO` (grau, adjacência, extremos), um trecho cujas duas pontas
  caem no mesmo nó (dentro da tolerância de encaixe) deixa de contribuir
  para grau/adjacência/cruzamentos daquele nó — mas seu mapeamento
  trecho→nó continua registrado, para que a atribuição de número sequencial
  consiga achar o nó compartilhado com o vizinho.
- **Numeração automática — percurso**: um trecho degenerado nunca aparece
  como candidato de percurso (não entra na pilha de bifurcação, não é
  visitado por retrocesso). Ele é resolvido assim que o nó em que ele cai é
  alcançado pela primeira vez durante o percurso (percurso normal, salto
  entre componentes, ou trecho inicial) — adicionado à sequência final ali
  mesmo, sem nunca alterar a posição de referência do percurso.
- **Numeração automática — atribuição de número**: nenhuma mudança na
  função de atribuição em si; como o nó do trecho degenerado não conta como
  cruzamento (grau real dos vizinhos), o mecanismo existente de "nó
  compartilhado que não é cruzamento → herda o número do anterior" já
  produz o resultado certo, desde que o trecho apareça na posição certa da
  sequência final.
- **Remoção de trecho de passagem — identificação de nó de passagem**: a
  contagem de pontas de trecho de um `COD_LOGRADOURO` num nó, usada para
  decidir se ele é nó de passagem, para de contar as pontas de trechos
  degenerados.
- **Remoção de trecho de passagem — montagem do segmento**: depois de
  identificar os segmentos de passagem normais (só com trechos reais), cada
  trecho degenerado cujo nó caia num ponto interno de algum desses segmentos
  (entre dois trechos reais consecutivos que compartilham aquele nó) é
  inserido na lista ordenada, na posição entre esses dois vizinhos.
- **Remoção de trecho de passagem — colapso**: nenhuma mudança em
  `colapsar`/`_estender`/`_incorporar_lado` — o comportamento já existente
  para um trecho cujas duas pontas coincidem (retorna a lista de
  coordenadas sem vértice novo) já produz o resultado esperado, e como ele
  nunca é o maior do segmento, nunca é escolhido trecho absorvedor.
- **Avisos**: os dois algoritmos emitem um aviso de feedback (`pushWarning`,
  seguindo o padrão já usado no `avisar_sem_codigo` e nos avisos de
  cruzamento fora de escopo) sempre que encontram um trecho degenerado —
  esteja ele dentro ou fora do contexto de nó de passagem. O texto do aviso
  cita `IDPKTRLOGR` e `COD_LOGRADOURO`.
- **Fora de contexto de nó de passagem**: se o nó de um trecho degenerado
  não corresponde a um nó de passagem real (é cruzamento, extremidade, ou o
  trecho está isolado sem vizinho real do mesmo código), nenhum dos dois
  algoritmos o toca — o aviso é emitido, mas o trecho permanece exatamente
  como está.
- Sem novo parâmetro de interface em nenhum dos dois algoritmos — o
  tratamento de trecho degenerado é sempre ativo, não é opt-in.

## Testing Decisions

- Só comportamento externo (resultado da numeração/remoção), não detalhes de
  implementação — mesmo padrão dos specs anteriores desta sessão.
- **Numeração automática**: testes contra `GrafoLogradouro` +
  `SequenciadorAutomatico` + `atribuir`, com um stub de `qgis.core` apoiado
  em geometria real (Shapely), como nos specs anteriores. Cenários
  sintéticos mínimos:
  - Trecho degenerado num nó interno com exatamente dois vizinhos reais do
    mesmo código (o caso do `33792`/`7644`) — numeração completa sem erro de
    gap, trecho degenerado recebe o mesmo número do segmento.
  - Trecho degenerado numa extremidade de um componente, logo antes de um
    salto para outro componente desconexo — o salto deve medir a distância
    certa a partir do vizinho real, não do self-loop.
  - Trecho degenerado num nó que já é cruzamento real (bifurcação de 3+
    ramos reais) — não deve ser removido do grafo nem confundir a contagem
    de cruzamento; apenas resolvido e avisado.
  - Trecho degenerado isolado (única feição do seu `COD_LOGRADOURO`, ou sem
    nenhum vizinho real por perto) — numeração ainda completa (ele recebe
    número 1 sozinho, já que hoje um logradouro de um trecho já funciona
    assim), com aviso.
  - Regressão: um `COD_LOGRADOURO` sem nenhum trecho degenerado numera
    exatamente como antes.
- **Remoção de trecho de passagem**: testes contra `segmentos_de_passagem` +
  `colapsar`, mesmo padrão dos specs de `quebra-entre-logradouros` e
  `remover-trechos-passagem`. Cenários sintéticos mínimos:
  - Trecho degenerado entre dois trechos reais que formam um segmento de
    passagem — o segmento colapsa incluindo o trecho degenerado; ele aparece
    em `apagar`, sem ganhar vértice no trecho absorvedor.
  - Trecho degenerado num nó de cruzamento real (3+ trechos, ou nó tocado
    por outro `COD_LOGRADOURO`) — não entra em `apagar`, avisado.
  - Trecho degenerado isolado — não entra em `apagar`, avisado.
  - Regressão: um `COD_LOGRADOURO` sem nenhum trecho degenerado colapsa
    exatamente como antes.
- **Verificação com dados reais** (manual, via QGIS/MCP sobre a camada
  `TRECHOLOGRADOURO` do owner TUFFI, como já feito no diagnóstico): rodar a
  numeração real nos quatro `COD_LOGRADOURO` que hoje falham (`57`, `1078`,
  `7644`, `8130`) e confirmar sucesso; rodar nos seis que já passavam e
  confirmar que o resultado (a sequência de números) não muda.

## Out of Scope

- Remover incondicionalmente um trecho degenerado fora de um contexto de nó
  de passagem (cruzamento, extremidade, isolado) — decisão explícita do
  `ADR-0008`, mantém o algoritmo de remoção dentro do que seu nome promete.
- Corrigir os 10 trechos degenerados já existentes na camada real — este
  spec corrige o comportamento dos algoritmos; a limpeza de dado em si (se
  desejada) fica para depois, fora deste trabalho.
- Qualquer parâmetro novo de interface nos algoritmos — o tratamento é
  sempre ativo.
- Mudança na tolerância de encaixe (`TOL_VERTICE`) ou na tolerância de
  continuação (`TOL_GAP`) — os valores atuais (0,05 m e 30 m) não mudam.
- Trechos com comprimento pequeno mas **acima** da tolerância de encaixe —
  esses já formam nós distintos e não são "trecho degenerado" pela
  definição deste spec.

## Further Notes

- `ADR-0008` (`docs/adr/0008-trecho-degenerado-como-no-de-passagem.md`) já
  registra a decisão e o trade-off entre remover incondicionalmente vs. só
  dentro de nó de passagem — este spec implementa exatamente o que ali foi
  decidido.
- `CONTEXT.md` já tem a entrada "Trecho degenerado" — nenhuma mudança de
  glossário prevista neste spec, só implementação.
- O diagnóstico completo (incluindo a reprodução do erro real via QGIS MCP
  sobre a camada `TUFFI.TRECHOLOGRADOURO`) está registrado na conversa que
  originou este spec; os números de `COD_LOGRADOURO`/`IDPKTRLOGR` citados
  aqui vêm de dados reais de produção, não são hipotéticos.
