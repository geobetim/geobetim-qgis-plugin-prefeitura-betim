# Trecho degenerado tratado como nó de passagem, não como candidato de percurso

Define o comportamento da **numeração automática** e da **remoção de trecho
de passagem** diante de um **trecho degenerado** — um trecho cujas duas
pontas caem no mesmo nó, dentro da tolerância de encaixe.

## Motivação

Investigando por que a numeração automática do `COD_LOGRADOURO 7644` falhava
com "gap acima da tolerância" mesmo os dados estando bem conectados (as
extremidades reais do logradouro ficam a 7,79 m, ~0,11 m e 19,24 m uma da
outra — bem dentro da tolerância de continuação de 30 m), a causa raiz foi o
`IDPKTRLOGR 33792`: um trecho de 0,028 m cujas duas pontas colapsam no mesmo
nó (a tolerância de encaixe padrão é 0,05 m). Isso cria um **self-loop** no
grafo — um "trecho" cujo grau conta duas vezes no mesmo nó.

O `SequenciadorAutomatico` empurra esse nó para a pilha de bifurcação na
primeira visita (grau ≥ 2 ali) e segue pelo ramo real primeiro. Como o
self-loop nunca desloca a posição do percurso, ele fica pendente até o
percurso esgotar o resto do componente e retroceder (LIFO) só para consumi-lo
por último — e é exatamente nesse retrocesso que a posição de referência do
salto entre componentes desconexos (`_continuar_disjunto`) volta para esse nó
interior, em vez de ficar na extremidade real onde o percurso já tinha
chegado. O salto calculado a partir daí (73 m a 526 m, nas oito tentativas de
trecho inicial testadas) nunca corresponde à distância real entre os
componentes do logradouro.

Uma checagem em toda a camada `TRECHOLOGRADOURO` (17.006 trechos, dados
reais) encontrou **10 trechos degenerados** distintos, em 10 `COD_LOGRADOURO`
diferentes; rodando a numeração real sobre eles, **4 falham** com esse mesmo
padrão de erro (57, 1078, 7644, 8130) e 6 passam ilesos — depende de onde o
self-loop cai na ordem de percurso. Não é um caso isolado do 7644.

A mesma causa (contagem de grau inflada pelo self-loop) também existe na
**remoção de trecho de passagem** (`identificacao.py`, `_no_de_passagem`),
só que com o efeito inverso: em vez de travar um percurso, ela impede que o
nó seja reconhecido como **nó de passagem** — o trecho degenerado nunca entra
em nenhum **segmento de passagem** (`if a == b: continue`) e sobrevive à
operação sem ser tocado, mesmo quando os dois vizinhos reais deveriam
colapsar através dele.

## Escolha

- **Trecho degenerado** vira conceito de domínio (`CONTEXT.md`): trecho cujas
  duas pontas caem no mesmo nó, dentro da tolerância de encaixe.
- Na numeração automática, ele é tratado como se estivesse sempre num **nó de
  passagem**: herda o **número sequencial do trecho** dos vizinhos reais que
  também tocam aquele nó, nunca entra como candidato de percurso, nunca
  disputa bifurcação, nunca é empilhado como junção pendente — é resolvido no
  momento em que o nó é alcançado, sem nunca mover `_no_atual`. Emite aviso
  no feedback (`IDPKTRLOGR` + `COD_LOGRADOURO`).
- Na remoção de trecho de passagem, `_no_de_passagem` deixa de contar as
  pontas do próprio trecho degenerado ao decidir se um nó é nó de passagem —
  os vizinhos reais voltam a formar segmento entre si normalmente. O trecho
  degenerado é inserido na lista ordenada do segmento que contém seus
  vizinhos (quando esse segmento existe) para ser absorvido pelo `colapsar`
  já existente, sem ganhar geometria própria — nunca é escolhido **trecho
  absorvedor** por ser sempre o menor. Também emite aviso.
- **Escopo deliberadamente limitado**: um trecho degenerado só é
  removido/renumerado quando o nó dele corresponde a um nó de passagem real
  entre dois trechos do mesmo logradouro. Fora desse contexto — isolado, num
  **cruzamento**, ou numa **extremidade** — nenhum dos dois algoritmos o
  toca; só o aviso é emitido. A alternativa considerada (remover
  incondicionalmente, em qualquer contexto) foi descartada por expandir o
  propósito da "remoção de trecho de passagem" para uma limpeza geral de
  geometria degenerada, que não é o que o nome do algoritmo promete.

## Consequências

- Corrige a numeração automática dos `COD_LOGRADOURO`s afetados sem mudar a
  semântica documentada da **tolerância de continuação** (distância do
  *último vértice numerado*) — a correção fica isolada em como o self-loop é
  tratado, não em como o salto é calculado.
- A remoção de trecho de passagem passa a de fato remover trechos
  degenerados que estejam dentro de um segmento de passagem — sem alterar
  `colapsar`/`absorcao.py`, que já lidava bem com esse caso uma vez que o
  trecho entra na lista ordenada.
- Um trecho degenerado isolado, ou num cruzamento/extremidade, continua sem
  tratamento automático — permanece como aviso de qualidade de dado para o
  operador corrigir na origem.
- Verificação por stub de `qgis.core`: casos sintéticos de self-loop em nó
  interior (bifurcação de 3+ ramos onde um é degenerado) e em extremidade;
  regressão dos `COD_LOGRADOURO` reais 7644, 57, 1078 e 8130 (os que falhavam
  antes da correção) e dos que já passavam, para confirmar que o resultado
  não muda para eles.
