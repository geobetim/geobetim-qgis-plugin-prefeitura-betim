# 03: Remoção de trecho de passagem — trecho degenerado funde mesmo em cruzamento real

**What to build:** reverte parte do ticket 02 (ADR-0008): um **trecho
degenerado** passa a fundir sempre com o maior trecho real do mesmo
`COD_LOGRADOURO` que tocar seu nó — mesmo que esse nó seja um **cruzamento**
real (bifurcação de 3+ trechos reais do mesmo logradouro, ou nó tocado por
outro `COD_LOGRADOURO`). O cruzamento sobrevive; só o registro do trecho
degenerado desaparece, sem nenhuma extensão de geometria (o vizinho já tem,
por construção, um vértice bem ali). As duas exceções do ADR-0008
continuam: nó bloqueado por **camada de quebra** (sinal explícito do
operador) e trecho degenerado isolado (nenhum vizinho real) continuam sem
fusão automática, só aviso. Ver [ADR-0009](../../../docs/adr/0009-trecho-degenerado-funde-mesmo-em-cruzamento.md).

**Blocked by:** 02 (Remoção de trecho de passagem — trecho degenerado
absorvido no segmento)

**Status:** done

_Motivado por um caso real encontrado depois do ticket 02: o
`IDPKTRLOGR 33792` (`COD_LOGRADOURO 7644`) continuava sem ser removido
porque o nó onde ele cai também é tocado pelo trecho `33784`
(`COD_LOGRADOURO 1078`) — um cruzamento real, fora do escopo do ADR-0008. O
operador decidiu que a distinção não deveria valer para trecho degenerado._

_`trechos_degenerados_absorviveis` (que dependia de `_no_de_passagem` e de
checar se os vizinhos colapsaram) foi substituída por
`trecho_degenerado_fundivel` (`identificacao.py`): acha, entre os trechos
reais do mesmo código que tocam o nó do degenerado, o maior por comprimento
(`maior_por_comprimento`, antes `_maior`, agora pública em `absorcao.py`,
reaproveitada sem duplicar o critério de desempate do trecho absorvedor).
Se o nó estiver bloqueado por camada de quebra, ou não houver nenhum
vizinho real, devolve `None` (sem fusão)._

_Descoberta importante durante a implementação: a primeira tentativa
montava um "segmento" de 2 elementos `[maior_vizinho, degenerado]` e
alimentava no `colapsar` já existente (para reaproveitar `_estender` sem
alterar `absorcao.py`). Isso falhava sempre que o vizinho escolhido já
tinha sido estendido pela fase 1 normal (`segmentos_de_passagem`): o nó do
degenerado, depois da extensão, passa a ser um ponto **interno** da
geometria do vizinho, não mais uma das suas duas pontas — e `_estender` só
sabe anexar pela ponta. Investigando por quê isso nunca é um problema:
o nó do trecho degenerado só existe porque, na indexação
(`IndiceDeNos`), uma ponta do vizinho já cai dentro da tolerância de
encaixe **desse mesmo nó** — ou seja, o vizinho **sempre** já tem um
vértice ali, seja na geometria original, seja herdado de um colapso normal
(a extensão de segmento de passagem preserva todos os vértices do trecho
absorvido, incluindo essa ponta). A fusão do trecho degenerado nunca
contribui um ponto novo — é só apagar o registro dele. A implementação
final não chama `colapsar` para o trecho degenerado: só identifica o
vizinho (para reportar/decidir se funde) e adiciona o id à lista de
apagar. `algoritmo.py` também mudou: o `if not segmentos: continue` que
pulava o resto do laço foi removido, porque a fusão do degenerado agora
precisa rodar mesmo quando não há nenhum segmento de passagem comum
(exatamente o caso do cruzamento real)._

- [x] Trecho degenerado num cruzamento real com outro `COD_LOGRADOURO` funde
      com o maior vizinho real do mesmo código — sem nenhuma extensão de
      geometria em nenhum dos dois trechos envolvidos
- [x] Trecho degenerado numa bifurcação real de 3+ trechos do mesmo código
      (sem outro código envolvido) também funde com o maior dos vizinhos
- [x] Dois trechos degenerados no mesmo `COD_LOGRADOURO` — um dentro de um
      segmento de passagem comum, outro num cruzamento real — fundem
      corretamente, sem uma fusão interferir na outra
- [x] Trecho degenerado isolado (nenhum vizinho real) continua sem fusão,
      só aviso
- [x] Nó bloqueado por camada de quebra continua impedindo a fusão, só
      aviso
- [x] Regressão: `colapsar`/`absorcao.py` sem nenhuma alteração
- [x] Verificado contra a camada real (`TUFFI.TRECHOLOGRADOURO`, plugin
      recarregado no QGIS): rodando o algoritmo real (via
      `execute_processing`, seleção do `COD_LOGRADOURO 7644`,
      `NUMERAR_APOS=false`) o `IDPKTRLOGR 33792` foi de fato excluído da
      camada (12 feições restantes em vez de 13) — `33789` e `33791`
      permanecem com o mesmo `LENGTH` de antes, confirmando que nenhuma
      geometria foi alterada

_Code review (`/code-review --level high`) encontrou e corrigiu: docstring
do módulo `identificacao.py` ainda descrevia o mecanismo abandonado (montar
um segmento de 2 elementos e alimentar em `colapsar`) — reescrito para
descrever o mecanismo final (sem geometria nova); e `ids_cod` sendo
reconvertido para `set` a cada trecho degenerado dentro do laço — movido
para o chamador (`algoritmo.py`), convertido uma vez por `COD_LOGRADOURO`._
