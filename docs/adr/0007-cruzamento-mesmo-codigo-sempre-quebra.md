# Cruzamento no mesmo COD_LOGRADOURO sempre quebra (revoga parte do ADR-0006)

Revoga a regra do [ADR-0006](0006-camada-de-trechos-fonte-obrigatoria-de-cruzamento.md)
que tratava cruzamento entre trechos do **mesmo** `COD_LOGRADOURO` sem nó
compartilhado como atípico (só gerava aviso no log, nunca dividia). A fase 0
da **remoção de trecho de passagem** passa a dividir esse cruzamento pelo
mesmo caminho já usado para `COD_LOGRADOURO` diferentes — sem distinguir a
forma do toque (ponta encostando no meio, ou um X sem vértice em nenhum dos
dois lados).

## Motivação

O caso real que motivou a reversão: `COD_LOGRADOURO 7640` — o trecho
`IDPKTRLOGR 33729` encosta no meio do traçado do trecho `33725` (mesmo
código), a ~0,51 m do nó entre `33722`/`33725`. É uma junção real das três
vias, não um dado mal digitalizado; a remoção de trecho de passagem deveria
dividir `33725` ali e deixar `33722` estendido até o ponto de toque no
colapso, exatamente como faria se `33729` fosse de outro `COD_LOGRADOURO`.

Ao investigar por que a fase 0 nem chegava a gerar o aviso de "atípico" para
esse caso, apareceu um problema mais fundamento: a primitiva de interseção
(`intersecao_interna`, `quebra.py`) usava só o teste exato do GEOS
(`QgsGeometry.intersects`) para achar o ponto de cruzamento — e esse teste
pode falhar por imprecisão numérica mesmo quando a distância real entre as
geometrias é irrisória (o caso do 7640: ponta de `33729` a ~4×10⁻¹⁰ m da
linha de `33725`, e ainda assim `intersects()` devolvia `False`). Uma
checagem em toda a camada `TRECHOLOGRADOURO` (16.716 trechos, dados reais)
confirmou que isso não é isolado: **208 pares** de trechos têm uma ponta a
≤ 0,05 m (a tolerância de encaixe padrão) do meio do traçado do outro sem o
GEOS reconhecer a interseção exata — 173 entre `COD_LOGRADOURO` diferentes
(a fase 0 já deveria estar dividindo esses, e não estava) e 35 no mesmo
código (o bucket "atípico").

Corrigida a primitiva para também contar esse "quase toque" (ponta a ≤ `tol`
do traçado da outra geometria, mesmo sem interseção exata), a distinção
"mesmo código é atípico" deixou de fazer sentido: o motivo original — tratar
como suspeita de dado mal digitalizado um cruzamento sem nó — se aplicava
igualmente a um cruzamento entre códigos diferentes, e esse já sempre
dividiu. Não havia uma razão de domínio para as duas situações terem
resultados diferentes; era um artefato de como a regra foi desenhada.

## Escolha

- Cruzamento entre trechos do **mesmo** `COD_LOGRADOURO` sem nó compartilhado
  passa a dividir, igual a um cruzamento entre códigos diferentes — sem
  parâmetro para desligar, e sem distinguir ponta-no-meio de um X puro.
- A primitiva de interseção interna (`quebra.py`) passa a reconhecer um
  quase toque — ponta de uma geometria a ≤ `tol` do traçado da outra — como
  ponto de interseção válido, além da interseção exata do GEOS. Vale tanto
  para a fase 0 (cruzamento entre logradouros) quanto para a fase 2 (quebra
  por camada de quebra), que reaproveitam a mesma primitiva.
- Não há mais nenhum caminho "só loga, não divide" na fase 0. O parâmetro de
  retorno `avisos` de `quebrar_cruzamentos_entre_logradouros` continua
  existindo (reservado para uso futuro), mas hoje nada o preenche.

## Consequências

- Um `COD_LOGRADOURO` com um cruzamento real interno (uma pista dupla que se
  reencontra, um retorno) passa a ganhar um nó de verdade ali, dividido pela
  fase 0 antes de qualquer colapso — evita que esse ponto seja engolido por
  um colapso de segmento de passagem que ignoraria a junção.
- Os outros 207 pares encontrados na checagem de toda a camada não são
  corrigidos por este ADR — só o algoritmo muda; da próxima vez que a
  remoção de trecho de passagem rodar sobre esses `COD_LOGRADOURO`s, o
  comportamento corrigido já se aplica.
- Verificação por stub de `qgis.core` (a primitiva com casos sintéticos de
  quase toque dentro/fora da tolerância; a fase 0 com o `7640` real e um X
  puro sintético no mesmo código; regressão do `7647`/`7643` do ADR-0006) e
  um teste ponta a ponta (fase 0 + fase 1) confirmando que `33722` fica
  estendido até o ponto de corte e o pedaço remanescente de `33725` não
  colapsa através dele.
