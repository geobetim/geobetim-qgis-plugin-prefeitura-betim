# Fusão de trecho degenerado estende a geometria do vizinho (corrige premissa do ADR-0009)

Corrige uma premissa errada do [ADR-0009](0009-trecho-degenerado-funde-mesmo-em-cruzamento.md):
a fusão de um **trecho degenerado** com o maior vizinho real **precisa**
estender a geometria desse vizinho — não é, como o ADR-0009 concluiu, uma
operação sem efeito geométrico.

## Motivação

Depois do ADR-0009 (`IDPKTRLOGR 33792` fundindo com `33789` mesmo no
cruzamento real com o `COD_LOGRADOURO 1078`), o operador testou no QGIS e
apontou: o trecho foi apagado, mas nenhum outro trecho foi estendido para
preencher o espaço dele — "não entendi".

Investigando com as coordenadas reais: `33791` termina no ponto A
(`585149.9219, 7799015.5775`); `33789` começa no ponto B
(`585149.9235, 7799015.5490`). A e B ficam a **2,85 cm** um do outro — só o
`33792` (que vai exatamente de A a B) fechava essa distância. `33791` e
`33789` **nunca se tocam diretamente**; a premissa do ADR-0009 ("o vizinho
já tem, por construção, um vértice bem ali") estava certa sobre o nó
*compartilhado* (dentro da tolerância de encaixe, para fins topológicos),
mas errada sobre a *geometria bruta*: apagar `33792` sem compensar deixa
esse vão real de 2,85 cm na camada.

A primeira tentativa de implementação (antes do ADR-0009 ser fechado)
já tinha passado por essa ideia — montar um "segmento" de 2 elementos
`[vizinho, degenerado]` e alimentar em `colapsar` — mas foi abandonada por
um bug diferente (a heurística de anel fechado, resolvida com o
pós-processamento do ADR-0008/ticket 02). Ao revisitar essa abordagem para
resolver o vão, apareceu um bug **novo**, nunca exercitado antes: a função
`_estender` (`absorcao.py`) fica ambígua quando o trecho sendo incorporado
(`r`) é ele mesmo curtíssimo — as duas pontas de `r` caem dentro da
tolerância da MESMA ponta da base, e a ordem fixa de verificação dos 4
ramos escolhe sempre o ramo errado (produz um no-op silencioso, sem aviso).
Um segundo bug relacionado apareceu em `_limpar_consecutivos`: mesmo depois
de `_estender` devolver o vértice novo corretamente (no lado que anexa por
`pn`, o fim da base), a limpeza de pontos consecutivos mantinha a ponta
antiga (a primeira do par) e descartava o vértice novo — porque os dois
caem dentro da tolerância um do outro, exatamente por o `r` ser curtíssimo.

## Escolha

- A fusão de um trecho degenerado (`fundir_trecho_degenerado`, nova função
  em `identificacao.py`) volta a alimentar `colapsar` com um segmento de 2
  elementos `[vizinho, degenerado]` — reaproveitando `_estender` sem
  alterar sua estrutura, só corrigindo a ambiguidade.
- `_estender` corrigida: quando as duas pontas de `r` caem dentro da
  tolerância da mesma ponta da base, a mais próxima é tratada como a
  duplicata (descartada) e a mais distante como o vértice novo. Para um
  `r` de comprimento normal isso nunca é ambíguo (só uma ponta cai perto),
  então nenhum colapso comum muda de resultado.
- `_estender` corrigida de novo: quando o vértice novo (do lado que anexa
  por `pn`) também cai dentro da tolerância da ponta antiga da base, a
  ponta antiga é descartada explicitamente em favor do vértice novo — em
  vez de deixar para `_limpar_consecutivos` decidir, que sempre mantém o
  mais antigo. O lado que anexa por `p0` já não tinha esse problema (o
  vértice novo entra primeiro na lista, e é `_limpar_consecutivos` que
  descarta a ponta antiga corretamente nesse sentido).
- `fundir_trecho_degenerado` devolve a nova geometria do vizinho, ou
  `None` quando não há extensão real (o vão já foi coberto por um colapso
  normal de segmento de passagem na mesma execução — cenário que já
  existia desde o ticket 02/03, sem geometria nova). Quem chama
  (`algoritmo.py`) atualiza `geom_nova` só quando há retorno; em qualquer
  caso, o trecho degenerado entra em `apagar`.

## Consequências

- `IDPKTRLOGR 33792` continua sendo apagado, mas agora `33789` passa a
  começar exatamente no ponto onde `33791` termina — sem vão. Verificado
  contra a camada real: `changed_geometries: 1` no buffer de edição (antes
  era 0), e a geometria de `33789` lida de volta confirma o novo vértice
  inicial idêntico à ponta de `33791`.
- Nenhuma mudança em `segmentos_de_passagem`/`_no_de_passagem`/`_ordenar` —
  só em `_estender` (dentro de `absorcao.py`) e na nova
  `fundir_trecho_degenerado` (`identificacao.py`).
- Verificação por stub de `qgis.core` com as coordenadas reais do `7644`
  (fecha o vão, sem tocar no outro vizinho); regressão de todos os cenários
  do ADR-0008/0009 (segmento de passagem comum, bifurcação real, isolado,
  bloqueado por camada de quebra, colapso sem trecho degenerado, anel
  fechado comum) — todos continuam com o mesmo resultado de antes.
