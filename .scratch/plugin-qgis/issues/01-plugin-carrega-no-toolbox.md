# 01: Plugin carrega com o algoritmo no Processing Toolbox

**What to build:** O plugin instala no QGIS 3.28 e o algoritmo "Numeração de
trechologradouro por logradouro" aparece no Processing Toolbox, com os
parâmetros na tela — ainda sem numerar nada.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Pasta `plugin-qgis/` na raiz do repo, contendo o pacote instalável `numeracao_trechologradouro/`
- [x] `metadata.txt`: `name=Numeração de trechologradouro por logradouro`, `qgisMinimumVersion=3.28`, `version=0.1.0`, `author=Prefeitura de Betim`, `email=tuffisal@gmail.com`, `hasProcessingProvider=yes`, `description`/`about` curtos
- [x] `__init__.py` com `classFactory`; classe de plugin que registra e remove um `QgsProcessingProvider` no `initGui`/`unload`
- [x] Um `QgsProcessingAlgorithm` no provider, com `initAlgorithm` declarando: camada de entrada (`QgsProcessingParameterFeatureSource`, só linha — o toggle "apenas feições selecionadas" vem de graça), campo do código do logradouro, campo do número sequencial, tolerância de interseção de vértices (Double, default 0.05), tolerância de gap entre trechos (Double, default 30.0)
- [x] `processAlgorithm` só empurra no `feedback` os valores escolhidos dos parâmetros; sem saída
- [x] `python -m py_compile` limpo em todos os `.py`
- [x] Verificável: instalar no QGIS 3.28, o algoritmo aparece no grupo do provider, o diálogo mostra os 5 widgets + o toggle de seleção, rodar ecoa os parâmetros no log
