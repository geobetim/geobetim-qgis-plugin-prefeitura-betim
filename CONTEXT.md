# Prefeitura de Betim — Plugin QGIS

Plugin QGIS que reúne algoritmos de edição da camada de trechos-logradouros
(`betimtaurus:TRECHOLOGRADOURO`) — numeração automática dos trechos de um
logradouro na ordem espacial, e remoção/quebra de trechos de passagem.

## Language

**Trecho-logradouro** (ou **Trecho**):
Segmento de via — uma feição `LineString` da camada `betimtaurus:TRECHOLOGRADOURO`.
Identificado pela chave primária `IDPKTRLOGR`.
_Avoid_: segmento, link, aresta, feature.

**Logradouro**:
A via inteira, identificada por `COD_LOGRADOURO`. É o conjunto de todos os trechos
que compartilham o mesmo `COD_LOGRADOURO`; tem um nome em `NOM_LOGRADOURO`.
Um logradouro por vez fica ativo na ferramenta.
_Avoid_: rua, via, endereço.

**`IDPKTRLOGR`**:
Chave primária de um trecho na camada de origem. Único identificador estável de
um trecho. É gerado pelo Geomedia a partir de uma sequência do banco; um trecho
criado fora do Geomedia nasce sem `IDPKTRLOGR` e só é gravável depois de receber
o próximo valor dessa sequência.

**`COD_LOGRADOURO`**:
Identificador do logradouro. É o critério de filtro (`CQL_FILTER`) para carregar
todos os trechos de um logradouro e o campo do formulário de busca. Um trecho
com `COD_LOGRADOURO` nulo não pertence a logradouro nenhum: o **plugin do QGIS**
o desconsidera — não entra em escopo da **numeração automática** nem da
**remoção de trecho de passagem**, não conta como **cruzamento** ao encostar num
nó de outro logradouro, e trechos nulos não formam um "logradouro" entre si.

**`CODTRECHOLOGRADOURO`**:
O código gerado para um **segmento** de um logradouro: `COD_LOGRADOURO` com 5
caracteres (zeros à esquerda), `.`, e um incremental de 4 caracteres (zeros à
esquerda) — ex.: `01052.0001`. Incrementa a cada cruzamento; trechos contíguos
ligados só por nós de passagem compartilham o mesmo `CODTRECHOLOGRADOURO`. Não
existe na camada de origem; é montado fora dela, a partir do **número
sequencial do trecho** — os valores podem repetir entre trechos do mesmo
segmento.
_Avoid_: código do trecho (na interface pode aparecer como "código"), ID do trecho.

**Número sequencial do trecho**:
O inteiro incremental por segmento, antes da máscara — o `0001` de `01052.0001`
vira `1`. É o que o plugin do QGIS grava direto num atributo da camada; a máscara
(`CODTRECHOLOGRADOURO`) é montada depois, na consulta. Começa em 1, incrementa a
cada cruzamento, repete entre trechos do mesmo segmento. Um `COD_LOGRADOURO` cujo
atributo de número sequencial já esteja preenchido em pelo menos um trecho é
considerado já numerado e é ignorado numa nova rodada.
_Avoid_: incremental (fora de contexto), ordem do trecho.

**Extremidade** (ou **trecho-extremidade**):
Trecho cuja ponta livre não se conecta a nenhum outro trecho do logradouro —
um nó de grau 1 no grafo do logradouro.
_Avoid_: ponta, início/fim (ambíguos), terminal.

**Trecho inicial**:
O trecho por onde a numeração de um logradouro começa. Entre as extremidades do
logradouro, ordenadas pela distância ao canto inferior esquerdo (menor X, menor
Y) do MBR do logradouro inteiro (empate pelo menor `IDPKTRLOGR`), é a primeira,
nessa ordem, que permite numerar todos os trechos do logradouro — sem emperrar
numa bifurcação sem saída nem num vão acima da tolerância de continuação. Isso
importa quando o logradouro tem **trechos desconectados**: a extremidade mais
perto do canto pode estar colada a um vão, e começar por ela prenderia o
percurso do lado errado; a próxima extremidade nessa ordem é tentada até uma
funcionar. Se o logradouro não tem nenhuma extremidade (anel fechado), o trecho
inicial é o mais próximo daquele canto, iniciando pelo vértice mais próximo —
uma única tentativa, como antes.

**Nó** (ou **junção**):
Ponto onde pontas de trechos coincidem, dentro de uma pequena tolerância de
encaixe (equivalente a ~0,05 m no terreno). O grau de um nó é quantas pontas de
trechos ele reúne.

**Logradouro conectado-simples**:
Logradouro cujo grafo de trechos é um caminho linear único: um só componente,
exatamente dois nós de grau 1, nenhum nó de grau ≥ 3.

**Bifurcação**:
Nó de grau ≥ 3 no grafo do logradouro. A numeração automática percorre um ramo
até o fim e depois volta (percurso em profundidade). Para efeito de numeração,
uma bifurcação também é um cruzamento.

**Cruzamento**:
Nó tocado por um trecho de outro logradouro (outro `COD_LOGRADOURO`), ou onde o
próprio logradouro bifurca. Na numeração, o código incrementa a cada cruzamento.
Na **remoção de trecho de passagem**, uma feição de **camada de quebra** encostando
no nó também o torna cruzamento — para uma feição poligonal, "encostar" é estar
perto da **borda** dela, não simplesmente cair dentro da área. Um trecho que
**cruza** (mesmo sem compartilhar nó — vértice só de um lado, ou nenhum) um
trecho de outro `COD_LOGRADOURO` **na própria camada de trechos** também é
cruzamento ali: a camada de trechos é fonte obrigatória de cruzamento na
remoção de trecho de passagem, sempre, independente de qualquer **camada de
quebra** configurada — ver **Remoção de trecho de passagem**.
_Avoid_: interseção, esquina.

**Nó de passagem**:
Nó de grau 2 que reúne apenas dois trechos do mesmo logradouro e nenhum outro
trecho. Na numeração, o código não incrementa: os dois trechos ficam no mesmo
segmento. Na **remoção de trecho de passagem**, um nó só é de passagem se, além
disso, nenhuma feição de **camada de quebra** encostar nele (na borda, se a
feição for poligonal).
_Avoid_: nó de continuação.

**Trecho degenerado**:
Trecho cujas duas pontas caem no mesmo **nó**, dentro da tolerância de encaixe
— não representa deslocamento espacial real (ex.: um trecho de 0,03 m cujo
início e fim colapsam no mesmo ponto). Na **numeração automática**, o nó onde
ele cai é tratado como **nó de passagem** entre os trechos reais que também o
tocam: ele herda o mesmo **número sequencial do trecho** dos vizinhos, nunca
entra no percurso nem na pilha de bifurcação, e nunca desloca a posição do
percurso — resolvido assim que seu nó é alcançado, não por encadeamento. Na
**remoção de trecho de passagem**, ele sempre funde com o maior trecho real do
mesmo `COD_LOGRADOURO` que tocar seu nó — mesmo critério do **trecho
absorvedor** (maior comprimento, empate pela chave primária ou pelo menor
`IDPKTRLOGR`) — mesmo que esse nó seja um **cruzamento** real (com outro
`COD_LOGRADOURO`, ou bifurcação de 3+ trechos reais do mesmo logradouro): o
cruzamento sobrevive (o vizinho já tem, por construção, um vértice bem ali —
a fusão nunca precisa estender geometria, só apaga o registro do trecho
degenerado; ver ADR-0009, que revoga parte do ADR-0008). Exceções: um nó
bloqueado por **camada de quebra** continua impedindo a fusão ali (sinal
explícito do operador, ver **Camada de quebra**); e um trecho degenerado
isolado — sem nenhum trecho real do mesmo
`COD_LOGRADOURO` tocando o nó — não tem para onde fundir, então não é tocado.
Nesses dois casos, e sempre que um trecho degenerado é encontrado, os dois
algoritmos emitem aviso.
_Avoid_: trecho de comprimento zero, laço, self-loop.

**Segmento**:
Sequência maximal de trechos de um logradouro que são consecutivos na sequência e
estão ligados apenas por nós de passagem. Todos os trechos de um segmento
compartilham o mesmo `CODTRECHOLOGRADOURO`.
_Avoid_: quarteirão, quadra, lance, bloco, face de quadra.

**Segmento de passagem**:
Um **segmento** com dois ou mais trechos — uma sequência de trechos do mesmo
`COD_LOGRADOURO` ligados só por **nós de passagem**, terminada em cruzamento,
bifurcação ou extremidade nas duas pontas. É o alvo da **remoção de trecho de
passagem**: colapsa num trecho só. Um segmento de um trecho só não é segmento de
passagem e não é tocado.
_Avoid_: trecho de passagem (é o nó, não o trecho), cadeia.

**Trecho de passagem**:
Trecho cujas **duas** pontas são **nós de passagem** — está no interior de um
**segmento de passagem**, sem nenhum **cruzamento** nem **extremidade** encostado.
A identificação é topológica, no grafo restrito ao mesmo `COD_LOGRADOURO`. Sozinho
não é a unidade da operação: o que colapsa é o **segmento de passagem** inteiro
que o contém.
_Avoid_: trecho de ligação, conector, trecho redundante.

**Trecho absorvedor**:
Na **remoção de trecho de passagem**, o maior trecho (por comprimento) do
**segmento de passagem** que colapsa — empate pelo **menor** `IDPKTRLOGR`. É o
único registro que sobrevive ao colapso: sua geometria é estendida para passar
por **todos** os vértices dos demais trechos do segmento, na ordem; os outros são
apagados. Num **segmento de passagem fechado** (anel), o absorvedor vira um
trecho fechado que **começa e termina no nó de fechamento** do segmento — o nó
compartilhado pelas duas pontas do segmento, em geral um **cruzamento** — para
quem encostava ali continuar encostando numa ponta do trecho, não no meio.
_Avoid_: trecho pai, trecho principal, trecho vencedor.

**Trecho desconectado**:
Trecho (ou grupo de trechos) que forma um componente separado do restante do
grafo do logradouro — não compartilha nó (dentro da tolerância de encaixe) com
nenhum outro trecho do mesmo `COD_LOGRADOURO`. O caso típico é o **eixo
paralelo**: pista dupla, canteiro central ou qualquer situação em que o
logradouro tem dois traçados que correm perto um do outro sem se tocar. A
numeração automática o alcança encadeando pela proximidade (ver **Tolerância
de continuação**).
_Avoid_: trecho de passagem entre eixos paralelos que **compartilham** nó
(isso é só uma bifurcação comum — ver **Cruzamento** — não um trecho
desconectado; não envolve a tolerância de continuação).

**Tolerância de continuação**:
Distância máxima (30 m) permitida entre o último vértice numerado e a ponta do
próximo **trecho desconectado** do mesmo logradouro para a numeração encadear
através do vão. Existe para os casos de eixo paralelo (pista dupla): ao
terminar um lado, a numeração pula pro trecho ainda não numerado mais próximo
do último vértice numerado, contanto que essa distância caiba na tolerância.
Não se aplica a trechos que já compartilham nó — esses são cruzamento
(**bifurcação**) comum, resolvido no percurso normal, sem gap. Acima da
tolerância, a numeração daquele logradouro falha com erro.

**Sequência de trechos**:
A ordem linear total sobre todos os trechos de um logradouro usada para numerar.
Nenhum trecho do logradouro pode ficar fora dela.
_Avoid_: rota, caminho, lista.

**Numeração automática**:
Processo, sem intervenção humana, que produz a sequência de trechos de um
logradouro: parte do **trecho inicial**, percorre em profundidade (na bifurcação,
segue a continuação mais reta e depois volta) e encadeia trechos disjuntos pela
proximidade dentro da **tolerância de continuação**. No **plugin do QGIS**, roda
para cada `COD_LOGRADOURO` em escopo.

**Plugin do QGIS** (ou **Conjunto de algoritmos da Prefeitura de Betim**):
Um plugin QGIS com um provider do Processing ("Prefeitura de Betim") que reúne
os algoritmos de edição da camada de trechos, agrupados por escopo ("Trecho
logradouro"). Roda dentro do QGIS sobre uma camada de trechos carregada — sem
Oracle direto, sem HTTP. Todo algoritmo do conjunto grava **na edição** da
camada — os valores ficam visíveis no mapa mas só são persistidos quando o
operador salva as edições, o que permite inspecionar antes e reverter tudo de uma
vez. Recebe o atributo de agrupamento (`COD_LOGRADOURO`) por parâmetro e atua,
por padrão, só nos `COD_LOGRADOURO` com feição selecionada — o operador desmarca
a opção para atuar na camada inteira. Algoritmos
atuais: **numeração automática** por logradouro e **remoção de trecho de
passagem**.
_Avoid_: script, ferramenta do QGIS (é um provider do Processing num plugin).

**Remoção de trecho de passagem** (algoritmo do plugin: "Quebrar e remover
trechos de passagem"):
Operação que colapsa cada **segmento de passagem** de um `COD_LOGRADOURO` num
trecho só. Roda em três fases, na edição da camada, como algoritmo do **conjunto
de algoritmos da Prefeitura de Betim**:

- **Fase 0 — quebra pela própria camada**: a **camada de trechos** é fonte
  **obrigatória** de cruzamento (sempre, sem parâmetro) — distinta das
  **camadas de quebra**, que são auxiliares e opcionais. Onde um trecho em
  escopo cruza qualquer outro trecho na mesma camada — nó compartilhado ou
  não, inclusive um cruzamento no meio do traçado sem nenhum vértice em
  qualquer dos dois lados, do mesmo `COD_LOGRADOURO` ou não — o trecho em
  escopo é dividido ali. Por padrão um código fora de escopo nunca é tocado,
  só serve de candidato de cruzamento — a menos que o operador ligue
  "Também quebrar o outro logradouro no cruzamento", quando o trecho de fora
  também é dividido ali, só isso, sem entrar em colapso nem em quebra por
  camada de quebra nessa execução. É o que permite um trecho **sozinho** (sem
  nenhum outro do mesmo `COD_LOGRADOURO` por perto) ganhar um nó de verdade
  onde cruza outro trecho, antes de qualquer colapso ser avaliado. A detecção
  conta um quase toque — qualquer ponto de um trecho a até a tolerância de
  encaixe do traçado do outro, não só suas pontas — como cruzamento, mesmo
  sem interseção exata (ver ADR-0007).
- **Fase 1 — colapso**: acha os segmentos de passagem (no grafo já com os nós
  da fase 0) e, em cada um, mantém o **trecho absorvedor**, estende sua
  geometria por todos os vértices dos demais e apaga o resto. As **camadas de
  quebra** entram aqui como fonte adicional de **cruzamento**: um nó tocado por
  feição de quebra não é nó de passagem, então o segmento para ali.
- **Fase 2 — quebra pelas camadas de quebra**: divide nas interseções
  **internas** com as camadas de quebra **todo trecho em escopo** — colapsado
  (geometria já estendida) ou não (geometria original). Não depende de ter
  colapsado na fase 1.

Só toca em trecho que precisa mudar: um trecho já bem delimitado (segmento de um
trecho só, sem cruzamento novo — da própria camada ou de camada de quebra — no
interior) fica intacto, mesmo `IDPKTRLOGR`. Não altera o **número sequencial do
trecho** — isso é papel da **numeração automática** (com "sobrescrever
numeração", já que a geometria mudou).
_Avoid_: dissolução, limpeza topológica.

**Camada de quebra**:
Camada **auxiliar** (linha ou polígono, opcional, até duas) da **remoção de
trecho de passagem** — não confundir com a **camada de trechos** em si, que
cumpre um papel parecido mas obrigatório na **fase 0** (ver **Remoção de trecho
de passagem**). Uma camada de quebra tem dois papéis:

- na **fase 1**, feição de quebra encostando num nó (dentro da tolerância de
  encaixe) torna esse nó **cruzamento** — o **segmento de passagem** não colapsa
  através dele, o que preserva trechos já partidos no lugar certo;
- na **fase 2**, interseções **internas** de feição de quebra com **qualquer**
  trecho em escopo (`tol < d < comprimento − tol`, colapsado ou não) dividem o
  trecho: o registro original fica com o primeiro pedaço, cada pedaço seguinte
  vira um registro novo, cópia dos atributos, com `IDPKTRLOGR` da sequência do
  Geomedia (ou nulo, com aviso).

Para uma feição **poligonal**, os dois papéis usam a **borda** do polígono, não a
área cheia — um ponto no interior, longe de qualquer borda, não é "encostar" nem
"cruzar". Interseção que cai num limite de trecho já existente não gera recorte —
a quebra ali já existe.
_Avoid_: camada de corte, camada de cruzamento (o corte é geométrico, não é o
**cruzamento** do glossário — embora, na fase 1, dispare um cruzamento).

**Sobrescrever numeração**:
Modo da **numeração automática** (no plugin do QGIS) que renumera um
`COD_LOGRADOURO` mesmo que o **número sequencial do trecho** já esteja preenchido.
Desligado por padrão — nesse caso um logradouro já numerado é ignorado. Serve
para depois de operações que mudam a geometria dos trechos (como a **remoção de
trecho de passagem**), que deixam a numeração anterior obsoleta.
_Avoid_: forçar numeração, recalcular.
