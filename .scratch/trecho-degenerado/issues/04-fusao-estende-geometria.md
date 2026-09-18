# 04: Remoção de trecho de passagem — fusão do trecho degenerado estende a geometria

**What to build:** corrige a premissa do ticket 03 (ADR-0009): a fusão de um
**trecho degenerado** com o maior vizinho real precisa estender a
geometria desse vizinho, fechando o vão real (dentro da tolerância de
encaixe, mas não coincidente) que existia entre ele e o outro lado do
trecho degenerado — o trecho degenerado quase nunca tem as duas pontas
exatamente iguais; cada ponta costuma coincidir exatamente com um vizinho
diferente. Ver [ADR-0010](../../../docs/adr/0010-fusao-de-trecho-degenerado-estende-geometria.md).

**Blocked by:** 03 (Remoção de trecho de passagem — trecho degenerado
funde mesmo em cruzamento real)

**Status:** done

_Motivado por feedback direto do operador depois de testar o ticket 03 no
QGIS: "apagou o trecho 33792 mas não estendeu um outro trecho para
preencher o espaço dele". Investigando com as coordenadas reais do
`COD_LOGRADOURO 7644`: `33791` termina no ponto A, `33789` começa no ponto
B, A e B ficam a 2,85 cm um do outro — só o `33792` fechava essa distância;
`33791` e `33789` nunca se tocam diretamente. A implementação anterior
(ticket 03) só verificava se o `IDPKTRLOGR` desaparecia, nunca se a
geometria do vizinho de fato mudava — por isso não capturou esse vão._

_Dois bugs latentes em `absorcao.py`, nunca exercitados antes (porque
nenhum colapso normal incorpora um trecho tão curto quanto um trecho
degenerado):_

_1. `_estender`: quando o trecho sendo incorporado (`r`) é ele mesmo
curtíssimo, as duas pontas de `r` caem dentro da tolerância da MESMA ponta
da base ao mesmo tempo — a ordem fixa dos 4 ramos de verificação sempre
escolhia o ramo errado, produzindo um no-op silencioso (sem aviso).
Corrigido: a ponta de `r` mais próxima da base é tratada como duplicata
(descartada), a mais distante como o vértice novo._

_2. `_limpar_consecutivos`: mesmo com `_estender` corrigida, o vértice
novo (do lado que anexa por `pn`, o fim da base) caía dentro da tolerância
da ponta antiga — e a limpeza de consecutivos sempre mantém o mais antigo
dos dois, descartando justo o vértice novo. Corrigido dentro da própria
`_estender`: quando isso acontece, a ponta antiga é descartada
explicitamente, sem depender de `_limpar_consecutivos` para decidir. O
lado que anexa por `p0` (o início da base) não tinha esse problema — o
vértice novo entra primeiro na lista, e a limpeza já descarta a ponta
antiga corretamente nesse sentido._

_A fusão em si voltou a reaproveitar `colapsar` (nova
`fundir_trecho_degenerado` em `identificacao.py`), montando um "segmento"
de 2 elementos `[vizinho, degenerado]` — a abordagem que tinha sido
abandonada no ticket 02 por um motivo diferente (heurística de anel
fechado, que não se aplica a um segmento de 2 elementos). Quando o vão já
foi coberto por um colapso normal de segmento de passagem na mesma
execução, `fundir_trecho_degenerado` devolve `None` (nenhuma geometria
nova) e o trecho degenerado ainda é apagado — mesmo comportamento do
ticket 03 para esse caso específico._

- [x] Trecho degenerado num cruzamento real com outro `COD_LOGRADOURO`:
      o vizinho escolhido estende sua geometria para fechar o vão real com
      o outro vizinho (que nunca é tocado)
- [x] Regressão: vizinho já estendido por um colapso normal de segmento de
      passagem na mesma execução — nenhuma geometria nova, só apaga (sem
      erro)
- [x] Regressão: colapso normal de segmento de passagem, sem trecho
      degenerado envolvido, não muda de resultado
- [x] Regressão: anel fechado comum (sem trecho degenerado) não aciona a
      heurística de anel fechado por engano
- [x] Regressão: bifurcação real, isolado, bloqueado por camada de quebra
      — mesmo comportamento do ticket 03
- [x] Verificado contra a camada real (`TUFFI.TRECHOLOGRADOURO`, plugin
      recarregado): rodando o algoritmo real sobre o `COD_LOGRADOURO 7644`,
      o buffer de edição mostra `changed_geometries: 1` (antes era 0); a
      geometria de `33789` lida de volta começa exatamente no ponto onde
      `33791` termina — vão fechado, `33791` intocado
