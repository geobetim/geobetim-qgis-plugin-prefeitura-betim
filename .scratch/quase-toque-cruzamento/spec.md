# Spec: Quase toque na detecção de cruzamento (robustez numérica da fase 0)

**Status:** implementado

Corrige um bug de robustez numérica na fase 0 da **remoção de trecho de
passagem** (`.scratch/quebra-entre-logradouros/spec.md`, ADR-0006) e revisa a
regra de "cruzamento atípico" que esse ADR estabeleceu para o mesmo
`COD_LOGRADOURO`.

Motivado pelo `COD_LOGRADOURO 7640`: a ponta do trecho `IDPKTRLOGR 33729`
encosta no meio do traçado do trecho `33725` (mesmo `COD_LOGRADOURO`), a
~0,51 m do nó entre `33722`/`33725` — mas a **distância geométrica real entre
a ponta de `33729` e a linha de `33725` é ~4×10⁻¹⁰ m** (na prática, zero: a
ponta está em cima da linha). Ainda assim, o teste de interseção exata do
GEOS (`QgsGeometry.intersects`) devolve `False` para esse ponto. A fase 0
nunca chega a ver essa interseção — nem para dividir, nem para logar como
"atípico" — porque a primitiva usa exclusivamente o resultado exato do GEOS
para achar o ponto de cruzamento; o `tol` (tolerância de encaixe de vértices)
só é aplicado depois, para filtrar a distância ao longo da linha.

Uma checagem em toda a camada `TRECHOLOGRADOURO` (16.716 trechos, dados reais
do WFS de produção) confirmou que isso não é isolado ao 7640: existem **208
pares** de trechos em que a ponta de um está a ≤ 0,05 m (a tolerância de
encaixe padrão) do meio do traçado do outro, mas o teste exato do GEOS não
reconhece a interseção — **173 pares entre `COD_LOGRADOURO` diferentes** (a
fase 0 deveria estar sempre dividindo esses casos, hoje ignora
silenciosamente) e **35 pares no mesmo `COD_LOGRADOURO`** (o bucket
"atípico" do ADR-0006).

## Problem Statement

A fase 0 da remoção de trecho de passagem promete ser fonte **obrigatória**
de cruzamento entre `COD_LOGRADOURO` diferentes, "com ou sem nó
compartilhado". Na prática, ela só encontra o cruzamento quando o GEOS
reconhece uma interseção geométrica **exata** entre as duas linhas. Quando a
ponta de um trecho está extremamente próxima do traçado do outro — mas não
exatamente em cima dele, a ponto de o predicado exato do GEOS falhar por
imprecisão numérica — a fase 0 não vê nada: não divide, e (no caso do mesmo
`COD_LOGRADOURO`) nem loga o aviso de "atípico" que o ADR-0006 previu. O
cadastrador não tem nenhum sinal de que esse cruzamento existe.

Separadamente, o ADR-0006 decidiu que cruzamento no mesmo `COD_LOGRADOURO`
sem nó compartilhado é sempre atípico e nunca quebra. O caso real do 7640
mostra que isso é incorreto para pelo menos o caso onde a ponta de um trecho
encosta no meio de outro do mesmo código (uma junção real, não um dado mal
digitalizado) — deveria quebrar como qualquer outro cruzamento.

## Solution

1. A primitiva de interseção interna (`intersecao_interna` /
   `distancias_de_intersecao_interna`) passa a reconhecer um "quase toque":
   quando a ponta de uma geometria está a ≤ `tol` do traçado da outra, isso
   conta como um ponto de interseção interno ali (sujeito ao mesmo filtro
   `tol < distância_ao_longo < comprimento - tol` que já existe), mesmo que o
   teste exato do GEOS não reconheça a interseção. Isso corrige a fase 0
   (cruzamento entre `COD_LOGRADOURO` diferentes) e a fase 2 (quebra por
   camada de quebra), que reaproveitam a mesma primitiva.
2. A regra de "cruzamento atípico" do ADR-0006 é revogada: cruzamento entre
   trechos do mesmo `COD_LOGRADOURO` sem nó compartilhado passa a dividir
   igual a um cruzamento entre códigos diferentes — sem distinguir a forma do
   toque (ponta encostando no meio, ou um X sem vértice em nenhum dos dois
   lados). Não há mais um caminho "só loga, não divide" na fase 0.

## User Stories

1. Como cadastrador, quero que a remoção de trecho de passagem detecte um
   cruzamento entre logradouros diferentes mesmo quando a ponta de um trecho
   está apenas muito próxima (não exatamente sobre) o traçado do outro,
   para que a fase 0 cumpra a promessa de ser fonte obrigatória de
   cruzamento, mesmo com pequenas imprecisões de digitalização.
2. Como cadastrador, quero que um cruzamento no mesmo `COD_LOGRADOURO` sem nó
   compartilhado também divida o trecho (em vez de só aparecer no log), para
   que um logradouro com uma junção real entre dois de seus próprios trechos
   (ex.: uma pista voltando a se juntar) tenha essa junção corretamente
   identificada como cruzamento.
3. Como cadastrador, quero rodar a remoção de trecho de passagem no
   `COD_LOGRADOURO 7640` e ver `33722` estendido até o ponto onde `33729`
   toca `33725`, com `33725` dividido ali, para que a topologia reflita a
   junção real das três vias.
4. Como cadastrador, quero que a fase 2 (quebra por camada de quebra) também
   se beneficie da mesma correção de robustez, para que uma feição de quebra
   cujo vértice quase-mas-não-exatamente toca um trecho em escopo ainda
   divida esse trecho.
5. Como desenvolvedor mantendo o plugin, quero que a correção fique na
   primitiva geométrica compartilhada (`quebra.py`), não duplicada em cada
   fase, para que fase 0 e fase 2 não divirjam de novo no futuro.
6. Como desenvolvedor, quero um teste unitário da primitiva com um caso
   sintético de "quase toque" (ponta a poucos milímetros do meio de uma
   linha, dentro da tolerância) e um caso de controle fora da tolerância
   (não deve detectar), para que a correção não dependa apenas dos dados
   reais do 7640.
7. Como desenvolvedor, quero um teste de integração da fase 0 reproduzindo o
   `COD_LOGRADOURO 7640` (33722/33725/33729) ponta a ponta — divisão de
   `33725`, extensão de `33722` no colapso, `33725` original apagado, novo
   registro para o pedaço remanescente — para que a mudança de política do
   mesmo código seja verificada de forma equivalente ao que já existe para o
   `7647`/`7643`.
8. Como desenvolvedor, quero que os testes existentes do `7647`/`7643`
   (cruzamento entre códigos diferentes, ADR-0006) continuem passando sem
   alteração de resultado, para confirmar que a correção de robustez não
   muda o comportamento de um cruzamento que já era detectado antes.
9. Como cadastrador, quero que o log deixe de mencionar "atípico" para
   cruzamento no mesmo código (já que agora ele divide), e que a mensagem de
   conclusão da fase 0 continue contando quantos trechos foram divididos e
   quantos registros novos foram criados, sem distinguir mesmo código de
   código diferente nessa contagem.
10. Como cadastrador, quero que a ordem de leitura da topologia original
    (nunca o resultado já cortado de outro trecho do mesmo laço) continue
    valendo depois da correção, para que o resultado não passe a depender da
    ordem de visita dos trechos em escopo.

## Implementation Decisions

- **`intersecao_interna(linha, geometria, tol)`** (`quebra.py`): além do ponto
  de interseção exata do GEOS (via `linha.intersection(geometria)`), também
  testa cada ponta de `linha` contra `geometria` (e, simetricamente, cada
  ponta de `geometria` contra `linha`) por distância: se a distância for
  ≤ `tol`, essa ponta gera uma distância-ao-longo (via `lineLocatePoint`) como
  se fosse um ponto de interseção. O filtro existente
  (`tol < distância < comprimento - tol`) continua se aplicando do mesmo
  jeito — um quase toque perto de uma das próprias pontas de `linha` não deve
  gerar um corte espúrio colado na ponta.
- Deduplicação: candidatos vindos do GEOS exato e do teste de "quase toque"
  que caiam a ≤ `tol` de distância ao longo da linha um do outro contam como
  o mesmo ponto (já é o comportamento de `distancias_de_intersecao_interna`
  ao agregar múltiplas geometrias — só precisa continuar valendo quando as
  distâncias vêm de fontes diferentes dentro da mesma geometria).
- **`quebrar_cruzamentos_entre_logradouros`** (`quebra_entre_logradouros.py`):
  remove o ramo que hoje só gera aviso para o mesmo `COD_LOGRADOURO`
  (`avisos.append(...)`, sem cortar); um cruzamento no mesmo código passa
  pelo mesmo caminho de corte (`cortar`, ids temporários, ponto de corte
  marcado cruzamento) que já existe para código diferente — a única diferença
  é que a origem/destino do corte pode ser qualquer um dos dois trechos
  envolvidos (hoje o corte sempre acontece no `fid` em escopo sendo iterado;
  como agora os dois lados podem ser do mesmo código e ambos em escopo, os
  dois podem ser cortados, cada um no seu próprio ponto de interseção com o
  outro, na mesma passada — sem side-effect entre eles, já que a leitura
  continua sendo da topologia original).
- O parâmetro `avisos` de `quebrar_cruzamentos_entre_logradouros` deixa de
  receber a mensagem de "atípico"; a assinatura da função não muda (continua
  devolvendo a tupla de 7 posições), só passa a devolver uma lista de avisos
  tipicamente vazia para esse caso (pode continuar existindo para outros usos
  futuros, mas nada a emitir por este spec).
- `CONTEXT.md` ("Cruzamento", "Remoção de trecho de passagem") e ADR-0006
  precisam de atualização: a frase "cruzamento entre trechos do mesmo
  `COD_LOGRADOURO` sem nó compartilhado é atípico... só gera aviso" deixa de
  valer. Um novo ADR (ou uma seção de revisão no ADR-0006) documenta a
  reversão dessa decisão e o motivo (caso real do 7640 + achado de robustez
  numérica na checagem de toda a camada).
- Nenhum novo parâmetro de algoritmo: a tolerância usada no "quase toque" é a
  mesma `tol`/`TOL_VERTICE` que a fase 0 já recebe hoje.

## Testing Decisions

- Testes só de comportamento externo (entrada/saída das funções), como já é
  o padrão do projeto (stub de `qgis.core` com geometria real — interseção,
  distância, projeção ao longo da linha — nunca mock da API do QGIS).
- **Seam 1 — primitiva pura** (`intersecao_interna` /
  `distancias_de_intersecao_interna`, `quebra.py`): casos sintéticos.
  - Ponta de uma linha a poucos milímetros do meio de outra linha, dentro de
    `tol`: deve aparecer como distância interna válida.
  - Mesmo caso, mas com a ponta a uma distância maior que `tol`: não deve
    aparecer nada (caso de controle, evita que a correção fique
    "sempre detecta").
  - Ponta a ≤ `tol` mas caindo fora do intervalo interno (muito perto de uma
    das próprias pontas de `linha`, dentro de `tol < d < comprimento - tol`):
    continua filtrado, sem corte espúrio na ponta.
  - Caso de interseção exata do GEOS (já existente hoje): continua
    detectando, sem regressão.
- **Seam 2 — integração da fase 0** (`quebrar_cruzamentos_entre_logradouros`):
  - Reprodução do `COD_LOGRADOURO 7640` (`33722`, `33725`, `33729`, mesmo
    código): `33725` dividido no ponto de quase toque, `33722` não tocado
    nessa fase (só na fase 1, no colapso), id temporário criado para o
    pedaço remanescente de `33725`.
  - Reprodução do `COD_LOGRADOURO 7647`/`7643` (códigos diferentes, já
    cobertos por teste existente segundo `.scratch/quebra-entre-logradouros/`):
    continua passando sem alteração de resultado — confirma que a correção de
    robustez não regride o caso que já funcionava.
  - Caso sintético de dois trechos do mesmo código com um X puro (cruzando
    sem nenhum vértice em nenhum dos dois lados, bem longe de qualquer ponta)
    — agora também divide, nos dois lados, já que a exceção "atípico" deixou
    de existir.
  - Caso de controle: dois trechos (mesmo código ou não) com pontos a mais de
    `tol` um do outro — nenhuma divisão, nenhum falso positivo.
- Prior art: `.scratch/quebra-entre-logradouros/` já tem testes equivalentes
  para o caso de código diferente (X puro, múltiplas interseções); este spec
  estende essa mesma suíte, não cria um padrão novo.

## Out of Scope

- Qualquer mudança na fase 1 (colapso de segmento de passagem) ou na fase 2
  além de reaproveitar a primitiva corrigida — a lógica de absorção, chave
  primária e materialização de ids temporários não muda.
- Corrigir os outros 207 pares encontrados na checagem de toda a camada — a
  correção é no algoritmo; os dados de produção não são tocados por este
  spec. O cadastrador que rodar o algoritmo nesses `COD_LOGRADOURO`s vai
  passar a ver o comportamento corrigido na próxima execução.
- Revisar a numeração automática (`numeracao_trecho_logradouro`) — ela usa
  sua própria tolerância de gap (`Tolerância de continuação`) para trechos
  genuinamente desconectados; não usa `intersecao_interna` e não é afetada
  por este spec.
- Ajustar o valor da tolerância padrão (0,05 m) — fora de escopo; o pedido é
  fazer a detecção respeitar a tolerância já configurada, não mudar seu
  valor.

## Further Notes

- A checagem em toda a camada (16.716 trechos) foi feita fora do plugin
  (script Python ad-hoc com Shapely, mesma engine geométrica GEOS por baixo
  do `QgsGeometry`), só para dimensionar o problema antes deste spec — não
  faz parte da entrega; não precisa de teste nem de manutenção.
- O caso do `7647`/`7643` (ADR-0006) é uma boa referência de que a
  interseção exata do GEOS funciona bem para um cruzamento transversal
  "limpo" (X através do traçado, longe de qualquer vértice); o problema deste
  spec é especificamente a configuração degenerada em que o ponto de
  interseção está muito perto de (ou efetivamente sobre) uma ponta ou um
  vértice já existente — exatamente o tipo de caso que a tolerância de
  encaixe de vértices já existe para cobrir em outras partes do algoritmo.
