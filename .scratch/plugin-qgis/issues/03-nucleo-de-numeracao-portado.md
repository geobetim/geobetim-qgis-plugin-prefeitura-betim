# 03: Núcleo de numeração portado + ligado de ponta a ponta

**What to build:** O algoritmo numera de verdade: para cada `COD_LOGRADOURO` em
escopo e não descartado, grava o número sequencial inteiro por segmento em cada
trecho da camada, seguindo exatamente as regras da solução em C#.

**Blocked by:** 02

**Status:** done

- [x] Porte fiel do grafo (`GrafoLogradouro` já generalizado): índice de nós compartilhado + conjunto de `COD_LOGRADOURO` por nó no construtor; arestas, grau e cruzamento por alvo em `DefinirAlvo`; cruzamento = grau ≥ 3 **ou** mais de um `COD_LOGRADOURO` distinto no nó. O agrupamento de nó usa `QgsSpatialIndex` para achar o nó existente dentro da tolerância de interseção de vértices (não varredura linear)
- [x] Porte fiel do sequenciador (`SequenciadorAutomatico`): candidatos de partida = extremidades ordenadas pela distância (via `QgsPointXY.distance`) ao canto inferior esquerdo do MBR do alvo, empate pelo menor id; tenta cada candidato até um numerar todos os trechos; DFS com continuação mais reta usando `QgsVector.normalized()` + `QgsVector.dotProduct()`; pilha LIFO de bifurcações; `ContinuarDisjunto` com a tolerância de gap, lançando com a distância e os ids dos dois lados do vão
- [x] Porte fiel da atribuição (`AtribuidorDeCodigos`): percorre a ordem, `+1` quando não há nó compartilhado ou o nó é cruzamento, herda caso contrário, começa em 1; **sem** as validações de `99999`/`9999` (eram limites da máscara); grava `n` inteiro
- [x] Parser de geometria: itera os vértices do `QgsGeometry` (achata multipartes), primeiro vértice = início, último = fim — sem parsear WKT
- [x] `processAlgorithm`, por `COD_LOGRADOURO` em escopo e não descartado: monta (ou reaproveita) um grafo compartilhado da vizinhança — feições cujo retângulo envolvente intersecta o bbox dos trechos em escopo expandido pela tolerância de interseção (consulta ao `QgsSpatialIndex`) — roda `DefinirAlvo`, sequencia, atribui, e grava o inteiro em cada trecho sob sessão de edição do QGIS
- [x] Falha de topologia num `COD_LOGRADOURO` (vão acima da tolerância, DFS sem fechamento) → `feedback.pushWarning` com o código, a distância e os ids; nenhum trecho desse código é gravado; a execução segue
- [x] Resumo final no `feedback`: numerados, descartados por já numerados, falhados
- [x] Nenhuma rotina reimplementada que o QGIS já ofereça (distância, vetor, índice espacial, iteração de vértices são nativos); só o grafo/sequenciamento é escrito à mão
- [x] `python -m py_compile` limpo
- [x] Verificável no QGIS 3.28 sobre a camada real: `COD_LOGRADOURO` 1052 → segmentos 1 e 2; `COD_LOGRADOURO` 1171 → os dois componentes disjuntos encadeados pelo vão de ~26 m (mesmo resultado do serviço C#); um logradouro com vão real acima de 30 m → aviso + pulado, execução conclui
