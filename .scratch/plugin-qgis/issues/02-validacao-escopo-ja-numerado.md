# 02: Validação, escopo e "já numerado" — reportados sem numerar

**What to build:** Ao rodar, o algoritmo valida as entradas, descobre quais
`COD_LOGRADOURO` entrariam na numeração e quais são descartados por já estarem
numerados, e mostra um resumo — sem ainda gravar nenhum número.

**Blocked by:** 01

**Status:** done

- [x] `processAlgorithm` valida o CRS da camada como projetado (unidade metro); se for geográfico (graus), `QgsProcessingException` pedindo reprojeção para CRS métrico
- [x] Valida o campo de número sequencial como numérico (`Int`/`LongLong`/`Double` — o `NUMBER` do Oracle chega como real; o valor gravado é sempre `int`); se for texto, `QgsProcessingException` com mensagem clara _(revisto no ticket 09 de remover-trechos-passagem: real passou a ser aceito)_
- [x] Lê todas as feições de linha da camada carregada para memória (id, valor do campo de código, geometria) e monta um `QgsSpatialIndex`
- [x] Determina os `COD_LOGRADOURO` em escopo: distintos de toda a camada, ou distintos apenas entre as feições selecionadas quando "apenas selecionadas" estiver marcado (a camada inteira continua acessível para o grafo no ticket 03)
- [x] Regra de descarte: se **pelo menos 1** trecho de um `COD_LOGRADOURO` tem o campo de número sequencial não-NULL, o `COD_LOGRADOURO` **inteiro** é descartado — nenhum trecho dele é considerado, nem os que estão vazios
- [x] `feedback` recebe um resumo: quantos `COD_LOGRADOURO` em escopo, quantos descartados por já numerados, quantos ficariam para numerar — **sem numerar**
- [x] `python -m py_compile` limpo
- [x] Verificável no QGIS 3.28 sobre a camada real: contagens corretas; camada em CRS geográfico → erro claro; escolher campo de texto para o número sequencial → erro claro
