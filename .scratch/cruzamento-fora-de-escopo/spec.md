# Spec: Cruzamento fora de escopo e quase toque contra qualquer ponto da borda

**Status:** implementado

Duas extensões da fase 0 (quebra pela própria camada de trechos, ADR-0006 /
ADR-0007) da **remoção de trecho de passagem**, motivadas por casos reais
encontrados ao usar o algoritmo em produção — e uma renomeação do algoritmo
para refletir o que ele já faz hoje.

## Problem Statement

1. A detecção de "quase toque" (ADR-0007) só considera vértices de cada
   geometria como pontos candidatos — o primeiro/último de uma linha, ou
   (depois de uma correção já aplicada) todos os vértices de um anel
   fechado. Um trecho cuja ponta encosta no **meio de uma aresta reta** de
   uma **camada de quebra** poligonal, longe de qualquer vértice/canto, não
   é detectado — nem pelo teste exato do GEOS (é o mesmo problema de
   robustez numérica do ADR-0007), nem pelo teste por vértice atual.
2. A fase 0 promete ser fonte obrigatória de cruzamento, mas nunca modifica
   um `COD_LOGRADOURO` fora do escopo selecionado (ADR-0006: "o outro
   `COD_LOGRADOURO` nunca é tocado, mesmo fora de escopo"). Isso significa
   que, ao rodar a remoção só no `COD_LOGRADOURO` que o cadastrador está
   editando (`7643`, no caso real que motivou isto), um cruzamento real com
   um trecho de outro código fora de escopo (`33748`, do `7647`) nunca é
   quebrado — e a numeração automática, que só reconhece cruzamento por nó
   real compartilhado, nunca vê essa interseção.
3. O nome do algoritmo ("Remover trechos de passagem") não reflete que ele
   também quebra trechos — pela própria camada (fase 0) e por camadas de
   quebra auxiliares (fase 2) — desde a introdução da fase 0.

## Solution

1. A primitiva de interseção interna passa a testar **qualquer ponto** de
   cada geometria contra o traçado inteiro da outra, por distância — não só
   vértices. Concretamente: além do já existente (interseção exata do GEOS;
   vértices de uma geometria testados contra o traçado da outra), passa a
   testar também cada vértice do **trecho** (`linha`) contra a distância à
   geometria candidata inteira (`geometria.distance(vértice) <= tol`), o que
   cobre um vértice do trecho perto do meio de uma aresta da borda de
   quebra, e não é código morto como uma tentativa anterior (que só testava
   as duas pontas do trecho, sempre fora do intervalo interno) — vértices
   **internos** do trecho produzem uma distância interna válida.
2. Novo parâmetro booleano no algoritmo de remoção/quebra, desmarcado por
   padrão: "Também quebrar o outro logradouro no cruzamento". Quando
   marcado, um trecho de outro `COD_LOGRADOURO` fora do escopo que cruza um
   trecho em escopo (mesma detecção da fase 0, incluindo quase toque) também
   é dividido — só a divisão: o pedaço resultante não entra em colapso de
   segmento de passagem (fase 1) nem em quebra por camada de quebra (fase 2)
   nessa mesma execução, mesmo que o código de fora tivesse, ele também, um
   segmento de passagem colapsável. O código de fora nunca é adicionado ao
   escopo processado pelas fases 1/2. Desmarcado (padrão), o comportamento é
   o de hoje: nunca toca um código fora de escopo.
3. O algoritmo é renomeado para "Quebrar e remover trechos de passagem".

## User Stories

1. Como cadastrador, quero que um trecho de uma camada de quebra poligonal
   cujo ponto de toque fica no meio de uma aresta (não perto de nenhum
   canto) ainda seja reconhecido como quase toque, dentro da tolerância de
   encaixe, para que a quebra por camada de quebra funcione com a mesma
   robustez numérica que a fase 0 já ganhou.
2. Como cadastrador, quero rodar "Quebrar e remover trechos de passagem" só
   no `COD_LOGRADOURO 7643` e, marcando a nova opção, ver o trecho `33748`
   (do `COD_LOGRADOURO 7647`, fora do escopo que selecionei) dividido no
   ponto onde cruza `7643`, para que a numeração automática, rodada depois,
   reconheça esse ponto como cruzamento (nó com mais de um código) e não dê
   o mesmo número sequencial para `33773` e `33803`.
3. Como cadastrador, quero que essa opção venha **desmarcada por padrão**,
   para que quem já usa o algoritmo hoje não veja um código que não
   selecionou sendo alterado sem pedir.
4. Como cadastrador, quero que o código de fora, quando dividido por essa
   opção, não seja processado além do corte — nenhum colapso de segmento de
   passagem nem quebra por camada de quebra nele nessa execução — para que
   o efeito da opção fique restrito ao cruzamento, sem processar um
   logradouro que eu não pedi para editar.
5. Como cadastrador, quero que o pedaço novo criado no código de fora receba
   `IDPKTRLOGR` da sequência do Geomedia, igual a qualquer outro pedaço
   novo da fase 0, para que ele já nasça com uma chave primária válida.
6. Como desenvolvedor mantendo o plugin, quero que o teste de robustez do
   "quase toque contra qualquer ponto" cubra tanto o trecho-contra-trecho
   (fase 0) quanto o trecho-contra-camada-de-quebra (fase 2), reaproveitando
   a mesma primitiva, para não duplicar a lógica em dois lugares.
7. Como cadastrador, quero ver o algoritmo listado como "Quebrar e remover
   trechos de passagem" no painel de Processing, para que o nome já deixe
   claro que ele também quebra, não só remove.
8. Como desenvolvedor, quero que o `name` interno do algoritmo (identificador
   estável usado por scripts/modelos do Processing) também mude para
   refletir o novo nome, com a documentação (`CONTEXT.md`, `metadata.txt`,
   `shortHelpString`) sincronizada.
9. Como cadastrador, quero que rodar a remoção/quebra sem marcar a nova
   opção continue produzindo exatamente o resultado de hoje — nenhum
   código fora de escopo tocado — para não ter nenhuma mudança de
   comportamento não solicitada.
10. Como cadastrador, quero que, se dois códigos fora de escopo diferentes
    cruzarem o mesmo trecho em escopo em pontos distintos, ambos sejam
    divididos (cada um no seu ponto), não só o primeiro encontrado.

## Implementation Decisions

- `intersecao_interna`/`distancias_de_intersecao_interna` (`quebra.py`):
  adiciona uma terceira fonte de distância — cada vértice de `linha`
  testado por `geometria.distance(vértice) <= tol`, convertendo para
  distância ao longo de `linha` via `lineLocatePoint` (exata, já que o
  vértice é um ponto conhecido de `linha`). As pontas de `linha` continuam
  sendo naturalmente filtradas pelo intervalo interno (`tol < d <
  comprimento - tol`); só vértices internos do trecho contribuem. Vale para
  quantos vértices o trecho tiver — sem limite artificial.
- `quebrar_cruzamentos_entre_logradouros` (`quebra_entre_logradouros.py`):
  ganha um parâmetro novo (booleano), por exemplo `quebrar_fora_de_escopo`.
  Quando verdadeiro, candidatos de `COD_LOGRADOURO` diferente do trecho em
  escopo também são cortados (hoje só servem de referência, nunca
  modificados) — usando exatamente a mesma primitiva e o mesmo mecanismo de
  id temporário/`origem_real`/`pontos_de_corte` já existente, só estendendo
  quem pode ser alvo do corte. O `COD_LOGRADOURO` de fora dividido nunca
  entra no conjunto de códigos processado pelas fases 1/2 do chamador
  (`algoritmo.py`) — a fase 0 devolve o pedaço, mas quem decide se ele entra
  no laço de colapso/quebra é o chamador, e ele não deve entrar.
- `algoritmo.py` (remoção): novo `QgsProcessingParameterBoolean`
  (`QUEBRAR_FORA_DE_ESCOPO`, `defaultValue=False`); passa esse valor para
  `quebrar_cruzamentos_entre_logradouros`; resolve chave primária do pedaço
  de fora pelo mesmo pipeline já usado para os pedaços em escopo (mesma
  chamada em lote a `resolver_chaves`, já que ambos entram em `novos_fase0`
  hoje — não precisa de uma segunda resolução separada); aplica
  `changeGeometry`/`addFeatures` no pedaço de fora do mesmo jeito que já
  aplica para um id real truncado em escopo.
- Renomear: `displayName()` → "Quebrar e remover trechos de passagem";
  `name()` → `quebrar_remover_trechos_passagem` (era
  `remover_trechos_passagem` — quem tiver um modelo do Processing
  referenciando o id antigo precisa atualizar manualmente; fora de escopo
  ajustar automaticamente). `shortHelpString`, `CONTEXT.md` ("Plugin do
  QGIS", "Remoção de trecho de passagem") e `metadata.txt` sincronizados
  com o novo nome e as duas novas capacidades.

## Testing Decisions

- Mesmo padrão já estabelecido: stub de `qgis.core` com geometria real
  (Shapely por baixo), sem mock da API do QGIS.
- **Quase toque contra qualquer ponto**: caso sintético com o vértice
  **interno** de um trecho a poucos milímetros do meio de uma aresta de uma
  camada de quebra poligonal (longe de qualquer canto) — deve dividir; caso
  de controle com a mesma configuração, mas fora da tolerância — não deve
  dividir; regressão dos casos já cobertos (`7640`, `7647`/`7643`, X puro
  sintético) continuando a passar.
- **Quebrar fora de escopo**: caso sintético com um trecho em escopo
  cruzando um trecho de outro código fora de escopo — com a opção
  desmarcada (comportamento de hoje, nenhuma mudança no de fora) e marcada
  (o de fora é dividido, ganha `IDPKTRLOGR` novo, e não aparece em nenhum
  segmento de passagem colapsado nem quebra de camada de quebra dessa
  execução). Se possível, reproduzir o caso real do `7643`/`33748` com dados
  do WFS, análogo ao teste de regressão do `7647`/`7643` já existente.
- **Renomeação**: só compilação (`py_compile`) e confirmação de que
  `metadata.txt`/`CONTEXT.md`/`shortHelpString` citam o novo nome — não é
  um comportamento testável por stub.

## Out of Scope

- Migração automática de modelos do Processing (`.model3`) que referenciem
  o `name()` antigo do algoritmo — fica a cargo de quem os mantém.
- Estender a numeração automática com sua própria fase de cruzamento pela
  própria camada — decisão já tomada (grilling anterior): confiar no
  cadastrador rodar a remoção/quebra antes, opcionalmente encadeada com a
  numeração (`.scratch/numeracao-apos-remocao/`).
- Qualquer mudança na fase 1 (colapso) ou na lógica de absorção — a fase 1
  continua restrita aos códigos em escopo, sem exceção para o pedaço de fora
  criado pela nova opção.
- Reorganização de pastas do projeto — coberta por
  `.scratch/reorganizar-plugin-raiz/`.

## Further Notes

- A correção "quase toque contra qualquer ponto" e a opção "quebrar fora de
  escopo" são independentes uma da outra tecnicamente, mas nasceram da mesma
  investigação (fase 0/ADR-0007) e compartilham a mesma seam de teste —
  por isso um spec só, mas podem virar tickets separados.
- O caso real do `7643`/`33748` só fica totalmente resolvido combinando esta
  opção com o encadeamento remoção→numeração
  (`.scratch/numeracao-apos-remocao/`): sem o encadeamento, o cadastrador
  ainda precisa rodar a numeração manualmente depois, mas o nó de cruzamento
  já vai existir de verdade na camada assim que a remoção/quebra rodar com a
  opção marcada.
