# 01: Prefactor — reestruturar o plugin em `prefeitura_betim/`

**What to build:** a pasta do plugin do QGIS passa a se chamar
`plugin-qgis/prefeitura_betim/` e o código fica organizado para receber um
segundo algoritmo sem duplicar utilidade. Um único `QgsProcessingProvider`
"Prefeitura de Betim" expõe os algoritmos, agrupados por escopo ("Trecho
logradouro"). O código comum a mais de um algoritmo mora num subpacote `shared/`;
cada algoritmo mora no seu próprio subpacote. Do ponto de vista do operador nada
muda: a numeração continua no Toolbox, no mesmo grupo, com os mesmos parâmetros e
o mesmo resultado.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] A pasta `plugin-qgis/numeracao_trechologradouro/` foi renomeada para
      `plugin-qgis/prefeitura_betim/` (nome válido como módulo Python); o
      `__init__.py`/`classFactory`, o `metadata.txt` e o `provider.py` continuam
      na raiz do pacote.
- [x] Existe um subpacote `shared/` que **não importa** de nenhum subpacote de
      algoritmo, com: (a) `topologia.IndiceDeNos` — índice de nós por tolerância
      de encaixe expondo, por nó, grau, `COD_LOGRADOURO` incidentes e trechos
      incidentes; (b) `camada.exigir_crs_metrico` + `camada.ler_camada` — checagem
      de CRS projetado com unidade em metros e leitura da camada inteira para
      estruturas em memória + índice espacial; (c) `edicao.edicao_sem_commit` —
      contexto que põe a camada em edição se preciso, abre um `beginEditCommand`,
      aplica as mudanças, fecha com `endEditCommand`, faz `triggerRepaint` e
      **nunca** `commitChanges()`.
- [x] O algoritmo de numeração e seu núcleo (grafo, sequenciador, atribuidor,
      erros) ficam em `numeracao_trecho_logradouro/`; o `QgsProcessingAlgorithm`
      da numeração está dentro desse subpacote. `GrafoLogradouro` passa a se
      montar sobre `shared.topologia.IndiceDeNos`.
- [x] Existe um subpacote `remocao_trecho_logradouro_passagem/` (só com o
      esqueleto por enquanto — docstring do pacote).
- [x] `provider.py` importa o algoritmo do subpacote e o adiciona ao provider;
      nenhum subpacote de algoritmo importa outro; `shared/` não importa dos
      subpacotes de algoritmo.
- [x] `metadata.txt`: `name=Prefeitura de Betim`, `description`/`about` descrevem
      o conjunto de algoritmos; `version=0.2.0`; demais chaves preservadas.
- [x] `python -m py_compile` passa em todos os `.py` do plugin; teste de grafo de
      import com stub de `qgis` resolve e `provider.loadAlgorithms()` roda;
      checagem funcional de `GrafoLogradouro` pós-refactor (grau, cruzamento por
      bifurcação, cruzamento por outro código, `outro_no`, `no_compartilhado`) OK.
- [ ] No QGIS 3.28 o provider "Prefeitura de Betim" carrega e a "Numeração de
      trechologradouro por logradouro" roda e grava o número sequencial igual a
      antes (verificação do operador — pendente).
