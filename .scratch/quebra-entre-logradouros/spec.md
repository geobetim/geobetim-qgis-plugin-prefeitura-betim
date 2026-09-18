# Spec: Quebra pela própria camada de trechos (cruzamento entre logradouros)

**Status:** ready-for-agent

Terceira fase da **remoção de trecho de passagem**, adicionada **antes** das
duas já existentes (`.scratch/remover-trechos-passagem/spec.md`,
`.scratch/segmento-fechado/spec.md`). Motivada pelo `COD_LOGRADOURO 7647`
(um único trecho, `IDPKTRLOGR 33748`) que cruza, no meio de seu traçado, o
`COD_LOGRADOURO 7643` sem que nenhum dos dois lados tenha nó ali — confirmado
com dados reais do WFS: o vértice de `33748` fica a ~2,8 mm de um nó real de
`7643` (junção de dois trechos dele), dentro da tolerância de 0,05 m.

## Problem Statement

A **remoção de trecho de passagem** só conhece cruzamento onde já existe um
**nó** — uma ponta de trecho. Quando um trecho de um logradouro cruza, no meio
do seu próprio traçado, o trecho de **outro** `COD_LOGRADOURO` — porque um dos
dois (ou os dois) nunca foi dividido ali —, esse ponto não é nó para
ninguém e o algoritmo nem chega a considerá-lo: nada colapsa (porque não há
segmento de passagem para colapsar — no caso do `7647`, um único trecho não
forma segmento nenhum) e nada quebra (porque "quebra" hoje só existe contra
**camadas de quebra**, auxiliares e opcionais, nunca contra a própria camada de
trechos). O cadastrador precisa editar a geometria manualmente para inserir o
nó que faltou na digitalização.

## Solution

A **camada de trechos** passa a ser, ela mesma, fonte **obrigatória** de
cruzamento na remoção de trecho de passagem — sempre, sem parâmetro para
desligar, além de qualquer **camada de quebra** auxiliar informada. Uma nova
**fase 0**, antes da fase 1 (colapso):

- Para cada trecho em escopo, acha os pontos onde ele cruza — com ou sem nó
  compartilhado hoje, inclusive um X sem vértice em nenhum dos dois lados — um
  trecho de **outro** `COD_LOGRADOURO` na mesma camada, dentro da vizinhança já
  carregada em memória (sem nova consulta).
- Divide o trecho em escopo nesses pontos, do mesmo jeito que a quebra por
  camada de quebra já faz: o registro original fica com o primeiro pedaço,
  cada pedaço seguinte vira um registro novo, com `IDPKTRLOGR` resolvido de
  imediato pela sequência do Geomedia (mesmo pipeline da fase 2 — aceita o
  mesmo risco de buraco na sequência se um pedaço vier a ser absorvido depois).
- **Nunca** toca o outro `COD_LOGRADOURO` — mesmo que ele esteja fora de
  escopo (por exemplo, com "apenas selecionadas" ligado processando só
  `7647`, `7643` fica intocado).
- O nó de cada ponto de corte é marcado **cruzamento** explicitamente (mesmo
  conjunto que hoje bloqueia nó de passagem por camada de quebra) — não
  depende de o outro `COD_LOGRADOURO` ter, ele também, um nó real ali.
- Um cruzamento entre dois trechos do **mesmo** `COD_LOGRADOURO` sem nó
  compartilhado era atípico (não quebrava, só aparecia no log) — revogado
  pelo ADR-0007: hoje divide igual a um cruzamento entre códigos diferentes.
  Ver `.scratch/quase-toque-cruzamento/`.

Isso faz o `7647` ganhar um nó de verdade onde cruza o `7643`, antes de a
identificação de segmento de passagem entrar em ação — mesmo sendo, hoje, um
único trecho.

## User Stories

1. Como cadastrador, quero que "Remover trechos de passagem" quebre um trecho
   onde ele cruza, no meio do traçado, um trecho de outro `COD_LOGRADOURO` na
   mesma camada — sem precisar configurar nenhuma camada de quebra para isso.
2. Como cadastrador, quero que essa quebra rode **sempre**, sem parâmetro para
   ligar/desligar — é a própria camada de trechos que a dispara, não uma
   opção.
3. Como cadastrador, quero que a detecção cubra os três casos: vértice de um
   lado coincide com nó do outro (como o `7647`/`7643`); os dois lados já têm
   nó ali (nada a fazer — já é cruzamento hoje); nenhum dos dois tem vértice
   ali (X geométrico real) — usando o mesmo cálculo de interseção que já
   existe para camadas de quebra, não uma heurística de proximidade.
4. Como cadastrador, quero que só o trecho do `COD_LOGRADOURO` **em escopo**
   seja dividido; o outro `COD_LOGRADOURO`, mesmo cruzando exatamente no mesmo
   ponto, nunca é alterado nesta execução — mesmo se ele também tiver um único
   trecho sem nó ali.
5. Como cadastrador, quero que, ao processar a camada inteira (sem "apenas
   selecionadas"), os dois lados de um cruzamento acabem divididos — cada
   `COD_LOGRADOURO`, no seu próprio turno em escopo, vê o outro como "trecho de
   outro código" e se divide onde cruza.
6. Como cadastrador, quero que um trecho com duas ou mais interseções internas
   com trechos de códigos diferentes (ex.: um trecho longo cruzando duas ruas
   transversais sem nenhuma delas ter nó nele) seja dividido em todos os
   pontos, numa única passada.
7. Como cadastrador, quero que dois trechos do **mesmo** `COD_LOGRADOURO` que
   se cruzam sem compartilhar nó (dado atípico, ex.: uma alça mal digitalizada)
   **não** sejam divididos por esta fase — só um aviso no log, para o
   cadastrador investigar o dado manualmente.
8. Como cadastrador, quero que o nó criado por essa quebra seja tratado como
   **cruzamento** na identificação de segmentos de passagem da fase 1, mesmo
   que o outro `COD_LOGRADOURO` não tenha, ele mesmo, nenhum nó ali — para o
   ponto de corte nunca virar candidato a nó de passagem e ser colapsado de
   volta.
9. Como cadastrador, quero que os registros novos criados por essa quebra
   sigam a mesma regra de hoje: cópia dos atributos do original, `IDPKTRLOGR`
   pela sequência do Geomedia (ou nulo com aviso, fora do caminho Oracle),
   nunca herdando o `IDPKTRLOGR` do original.
10. Como cadastrador, quero que um pedaço criado por essa quebra que a fase 1
    depois absorva (porque ficou parte de um segmento de passagem colapsado
    por outro motivo) seja simplesmente apagado como qualquer outro trecho
    absorvido — o `IDPKTRLOGR` que ele recebeu fica como buraco na sequência,
    aceitável como já documentado.
11. Como cadastrador, quero que essa quebra não precise de nenhuma nova
    consulta à camada: usa a vizinhança já carregada em memória para a fase 1
    (bbox do escopo, expandido pela tolerância), filtrando por
    `COD_LOGRADOURO` diferente.
12. Como cadastrador, quero um resumo no log separado para essa quebra —
    quantos trechos foram divididos por cruzarem outro logradouro, quantos
    registros novos saíram daí (com/sem `IDPKTRLOGR`) — distinto da contagem
    de registros novos pela quebra por camada de quebra (fase 2).
13. Como cadastrador, quero que, sem nenhum cruzamento entre `COD_LOGRADOURO`
    diferentes na vizinhança, o comportamento seja idêntico ao de hoje —
    nenhuma mudança de geometria, contagem ou aviso.
14. Como cadastrador, quero rodar "Remover trechos de passagem" no `7647` (com
    "apenas selecionadas") e ver `33748` dividido em dois, com o pedaço novo
    recebendo `IDPKTRLOGR` da sequência, e o `7643` permanecendo exatamente
    como estava.
15. Como cadastrador, quero que o comportamento de segmento de passagem (fase
    1, incluindo o caso de segmento fechado) e de camada de quebra (fase 2)
    continuem exatamente como são hoje — esta fase só acrescenta nós que faltam
    antes deles rodarem.
16. Como mantenedor, quero que a comparação de cruzamento use o mesmo cálculo
    geométrico (interseção + posição ao longo da linha) já usado pela quebra
    por camada de quebra, generalizado para aceitar geometrias já carregadas em
    memória em vez de exigir uma segunda `QgsVectorLayer`.
17. Como mantenedor, quero que um trecho criado por esta fase, antes de existir
    de fato na camada, participe da identificação de segmento e do colapso da
    fase 1 por um identificador interno que nunca colide com um id real de
    feição — só se torna uma feição de verdade (com `addFeatures`) na aplicação
    final da edição, junto com os demais registros novos.
18. Como mantenedor, quero um ADR registrando a decisão de tratar a própria
    camada como fonte obrigatória de cruzamento (trade-off: correção
    topológica automática versus custo de comparar cada trecho em escopo
    contra a vizinhança de outros códigos, e a complexidade do identificador
    temporário).
19. Como mantenedor do glossário, quero **Cruzamento**, **Remoção de trecho de
    passagem** e **Camada de quebra** já atualizados no `CONTEXT.md` (feito na
    modelagem) refletidos neste spec.

## Implementation Decisions

- **Nova fase 0**, antes da identificação de segmentos de passagem (fase 1) e
  da quebra por camadas de quebra (fase 2). Roda sobre a união de todos os
  `COD_LOGRADOURO` em escopo, como a fase 2 já faz — não dentro do laço
  por-código da fase 1.
- **Fonte da quebra**: os trechos da própria vizinhança (já carregada em
  memória para a fase 1) cujo `COD_LOGRADOURO` é **diferente** do trecho sendo
  avaliado. Sempre linha contra linha — a própria camada de trechos é sempre
  `LineString`, então não há papel de "borda de polígono" aqui (isso continua
  exclusivo das camadas de quebra auxiliares, que podem ser poligonais).
- **Primitiva reaproveitada**: a função de achar distâncias de interseção
  interna (`tol < d < comprimento − tol`) e cortar a polilinha, hoje escrita
  contra uma lista de `QgsVectorLayer` (as camadas de quebra), é generalizada
  para aceitar diretamente um iterável de geometrias já carregadas — a fase 2
  continua montando esse iterável a partir de `camada.getFeatures()`; a fase 0
  monta a partir dos dicionários de geometria da vizinhança, filtrados por
  código diferente.
- **Cruzamento entre o mesmo código, sem nó compartilhado**: detectado e
  **não** dividido — só gera aviso no log com os dois `IDPKTRLOGR` e o ponto.
  Fica de fora da fonte de quebra da fase 0 (que só considera outro código).
- **Marcação explícita de cruzamento**: cada ponto de corte da fase 0 entra no
  mesmo conjunto de nós bloqueados que a fase 1 já usa para as camadas de
  quebra (`nos_bloqueados` / equivalente) — não depende de o outro
  `COD_LOGRADOURO` ter um nó real ali. Isso garante que a divisão nunca seja
  colapsada de volta na fase 1.
- **Identificador temporário**: um pedaço criado pela fase 0 recebe um id só
  interno (fora do espaço de ids reais de feição do QGIS — ex.: um contador
  negativo próprio, nunca usado para nenhuma chamada à camada) para poder
  circular pelas mesmas estruturas em memória (coordenadas, geometria, índice
  de nós) que os trechos reais, até a fase de aplicação final. Só nesse ponto
  vira uma feição de verdade (`addFeatures`), junto com os registros novos da
  fase 2, na mesma ordem já estabelecida (alterar geometria → adicionar novos
  → apagar).
- **Chave primária resolvida na hora** (decisão do operador: pode gastar
  sequence em pedaço que a fase 1 vier a apagar depois — é aceitável, como já
  documentado para buracos de sequência). Cada pedaço da fase 0 chama
  `resolver_chaves` logo depois da própria fase 0, numa consulta batida por
  execução (independente da chamada da fase 2, que resolve as suas depois).
- **Vizinhança**: reaproveitada sem mudança — o bbox de escopo (crescido pela
  tolerância) já traz, via índice espacial, qualquer trecho de outro código
  cuja geometria cruze algum trecho do escopo (duas linhas que se cruzam têm,
  por definição, caixas envolventes que se sobrepõem).
- **Resumo no log**: nova contagem separada da quebra por cruzamento entre
  logradouros (trechos divididos, registros novos com/sem chave), distinta da
  contagem já existente da quebra por camada de quebra.
- **Novo ADR** (`docs/adr/0006`): a própria camada de trechos como fonte
  obrigatória de cruzamento — trade-off entre correção topológica automática e
  o custo/complexidade de comparar cada trecho em escopo contra a vizinhança
  inteira de outros códigos, mais o identificador temporário para pedaços
  ainda não persistidos. ADR-0004 e ADR-0005 permanecem válidos; ADR-0005 é
  reaproveitado (mesma resolução de chave), não alterado.
- `CONTEXT.md`: **Cruzamento**, **Remoção de trecho de passagem** (três fases)
  e **Camada de quebra** (distinta da própria camada, que é obrigatória) já
  atualizados na modelagem — nenhuma mudança adicional de glossário prevista
  aqui.

## Testing Decisions

- **Seam único, reaproveitado**: a primitiva de achar distâncias de interseção
  interna e cortar a polilinha — mesma usada nos testes de `quebra.py` desde o
  ticket 04 — agora recebendo geometrias diretamente (não só via
  `QgsVectorLayer`), testável com stub de `qgis.core`, sem QGIS real.
- Um segundo ponto de verificação, no mesmo estilo dos tickets 06–09 e do
  `segmento-fechado`: alimentar `identificacao.segmentos_de_passagem` e
  `absorcao.colapsar` com o resultado da fase 0 (trechos já divididos, nó de
  cruzamento marcado) e conferir que o comportamento de segmento de passagem
  continua correto — não é um seam novo, é o mesmo já usado nesses tickets.
- **Casos**, com stub de `qgis.core` e, para o principal, coordenadas reais do
  WFS:
  1. `COD_LOGRADOURO 7647`/`7643` reais: `33748` divide em dois pedaços no
     ponto do cruzamento (~585078.23, 7799018.59); o pedaço novo recebe uma
     chave da sequência (stub); `7643` sai idêntico (nenhuma geometria dele
     tocada); o nó do corte está marcado cruzamento.
  2. Cruzamento sintético em X puro (nenhum dos dois trechos tem vértice no
     ponto): ambos os lados, quando cada um está em escopo, dividem no ponto
     exato calculado pela interseção.
  3. Trecho com duas interseções internas com códigos diferentes: dois cortes,
     três pedaços, ids intermediários corretos.
  4. Dois trechos do **mesmo** código cruzando sem nó compartilhado: nenhuma
     divisão, um aviso no log com os dois ids.
  5. Regressão: `COD_LOGRADOURO` sem nenhum cruzamento com outro código —
     saída idêntica à antes desta fase (nenhum trecho tocado por ela).
  6. Um segmento de passagem que, depois da fase 0, tem um dos seus trechos
     recém-dividido: o pedaço perto do cruzamento não colapsa através do nó
     marcado cruzamento; o restante do segmento colapsa normalmente.
- Prior art: testes funcionais com stub de `qgis.core` desta base (tickets
  04–10, `segmento-fechado`) e verificação com dado real do GeoServer (WFS
  `betimtaurus:TRECHOLOGRADOURO`) usada nos tickets 06, 07 e aqui para o
  `7647`/`7643`.
- Verificação do operador no QGIS 3.28: rodar a remoção no `7647` (apenas
  selecionadas) → `33748` sai como dois trechos, o novo com `IDPKTRLOGR` real,
  `7643` sem nenhuma mudança; rodar sem "apenas selecionadas" numa área com
  mais de um cruzamento parecido → os dois lados de cada cruzamento dividem.

## Out of Scope

- Tocar o `COD_LOGRADOURO` do outro lado do cruzamento quando ele está fora de
  escopo — nunca acontece, por decisão explícita.
- Dividir por cruzamento entre trechos do **mesmo** `COD_LOGRADOURO` sem nó
  compartilhado — só aviso no log.
- Qualquer parâmetro para ligar/desligar esta fase — é sempre obrigatória.
- Mudança nas camadas de quebra auxiliares (fase 2), na identificação de
  segmento de passagem, no colapso ou no segmento fechado — comportamento
  intocado quando não há cruzamento entre códigos diferentes.
- Adiar a resolução da chave primária dos pedaços da fase 0 para depois da
  fase 1 — decisão explícita do operador: resolve na hora.
- Testes automatizados no repositório; mudanças no C#, na API ou no
  front-end.

## Further Notes

- Diagnóstico feito com dados reais do WFS: o vértice de `33748` (índice 1 de
  4) está a ~2,8 mm de um nó real de `7643` (junção de `33773`/`33803`),
  dentro da tolerância de 0,05 m — confirma que o caso é topologia incompleta
  do lado do `7647`, não geometria degenerada.
- A garantia de atomicidade já estabelecida (tudo calculado em memória antes
  de qualquer escrita na camada, aplicado num único `beginEditCommand`) precisa
  se manter: os pedaços da fase 0 só entram na camada de verdade no mesmo
  ponto de aplicação final que já existe hoje para os pedaços da fase 2.
