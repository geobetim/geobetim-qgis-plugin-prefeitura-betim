# 03: Algoritmo "Remover trechos de passagem" — identificação + absorção

**What to build:** um segundo algoritmo do Processing, "Remover trechos de
passagem", no grupo "Trecho logradouro". O operador escolhe a camada de trechos,
o atributo de agrupamento (`COD_LOGRADOURO`), se processa a camada inteira ou só
os `COD_LOGRADOURO` das feições selecionadas, e a tolerância de encaixe de
vértices (default 0,05 m). O algoritmo identifica topologicamente os **trechos de
passagem** de cada `COD_LOGRADOURO` em escopo, apaga cada um e estende o **trecho
absorvedor** para tapar o vão, aplicando tudo na edição da camada sem gravar em
definitivo. Sem camadas de quebra e sem resolução de chave primária nesta fatia.

**Blocked by:** 01

**Status:** done

_Implementado em `remocao_trecho_logradouro_passagem/`: `identificacao.py`
(nó de passagem / trecho de passagem), `absorcao.py` (`_componentes`,
`_ordenar_cadeia`, `_encadear`, `_estender`, `planejar`), `algoritmo.py`
(`RemoverTrechosPassagemAlgorithm`). Registrado em `provider.py`. Verificado com
stub funcional de `qgis`: A–B–C–D → 2 trechos; cruzamento/bifurcação no meio →
nenhum trecho de passagem; cadeia de 3 → divide entre os dois vizinhos externos;
anel de 4 sem âncora → maior mantido, geometria fecha._

- [x] O algoritmo aparece no Toolbox no grupo "Trecho logradouro" do provider
      "Prefeitura de Betim", com `name` `remover_trechos_passagem` e `displayName`
      "Remover trechos de passagem"; roda sem threading.
- [x] Parâmetros: camada de trechos (camada de linha gravável do projeto);
      "processar apenas os `COD_LOGRADOURO` das feições selecionadas" (booleano,
      default `False`); atributo de agrupamento (campo da camada); tolerância de
      encaixe de vértices (Double, default `0.05`, mínimo 0).
- [x] Camada em CRS geográfico → `QgsProcessingException` pedindo reprojeção para
      CRS métrico. "Apenas selecionadas" ligado e sem seleção → erro claro.
- [x] Escopo: sem a opção, todos os `COD_LOGRADOURO` distintos da camada; com a
      opção, os `COD_LOGRADOURO` das feições selecionadas. A camada inteira é
      lida para o grafo de qualquer forma.
- [x] Um trecho é **trecho de passagem** quando as duas pontas são **nós de
      passagem**: no grafo restrito ao mesmo `COD_LOGRADOURO`, grau 2, exatamente
      dois trechos do mesmo código no nó, nenhum outro `COD_LOGRADOURO`
      incidente, sem bifurcação. O conjunto é fixado sobre o grafo original,
      antes de qualquer edição.
- [x] Para cada trecho de passagem, o **absorvedor** é o maior vizinho (por
      `QgsGeometry.length()`) do mesmo `COD_LOGRADOURO` que não esteja no
      conjunto de remoção; empate pelo maior `IDPKTRLOGR`/id da feição. Numa
      cadeia de trechos de passagem sem nenhum vizinho externo, o absorvedor é o
      maior trecho da própria cadeia (mantido; os outros da cadeia são apagados).
- [x] A geometria do absorvedor é estendida para passar por **todos** os
      vértices de cada trecho removido que ele cobre, na ordem, do nó
      compartilhado até a ponta oposta, sem duplicar o nó.
- [x] Casos pulados com aviso, sem abortar: trecho de passagem com < 2 vértices;
      absorvedor que compartilha as duas pontas do removido (laço); trecho de
      passagem sem nenhum vizinho do mesmo código.
- [x] Os atributos do absorvedor não mudam — só a geometria. Nenhum número
      sequencial é lido ou escrito.
- [x] Tudo é aplicado na edição da camada num único `beginEditCommand`
      (geometrias alteradas, depois feições apagadas), com `triggerRepaint`, sem
      `commitChanges()`. Erro no meio desfaz o comando de edição.
- [x] Resumo no log: trechos de passagem removidos, absorvedores estendidos,
      `COD_LOGRADOURO` pulados (com motivo), mais a linha lembrando de salvar ou
      reverter as edições.
- [x] `python -m py_compile` limpo; grafo de import resolve com stub; testes
      funcionais de `identificacao`/`absorcao`/`planejar` passam.
- [ ] Verificação do operador no QGIS 3.28: um trecho de passagem conhecido some
      e o maior vizinho passa a cobrir o traçado dele; a cadeia `A—B—C—D` (nós
      internos de passagem) resulta em dois trechos; "Reverter" desfaz tudo num
      passo. (pendente)
