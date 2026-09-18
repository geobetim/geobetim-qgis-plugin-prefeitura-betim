# 01: Numerar após quebrar e remover

**What to build:** parâmetro booleano novo no algoritmo de remoção/quebra,
desmarcado por padrão: "Numerar os trechos após a remoção". Marcado, depois
de aplicar a remoção/quebra no escopo escolhido, o algoritmo lê a camada de
novo (já com a geometria atualizada no buffer de edição), monta o grafo e
numera automaticamente os mesmos `COD_LOGRADOURO` processados, sempre
sobrescrevendo a numeração anterior — sem expor essa escolha como
parâmetro. Reaproveita as mesmas funções puras que
`numeracao_trecho_logradouro` já usa (`GrafoLogradouro`,
`SequenciadorAutomatico`, `atribuir`), sem instanciar o
`QgsProcessingAlgorithm` da numeração como sub-algoritmo. Os parâmetros
compartilhados (atributo de agrupamento, "apenas selecionadas", tolerância
de encaixe de vértices) aparecem uma vez só na interface; os específicos da
numeração (atributo do número sequencial, tolerância de gap) ficam
separados, e só importam quando a opção está marcada.

**Blocked by:** None (can start immediately)

**Status:** done

_Implementado como método privado
`RemoverTrechosPassagemAlgorithm._numerar_codigos_afetados`, chamado depois
que o bloco `edicao_sem_commit` da remoção/quebra já fechou (ou no early
return de "nada a fazer", se `NUMERAR_APOS` estiver marcado mesmo assim) —
reaproveita `ler_camada`, `GrafoLogradouro`, `SequenciadorAutomatico`,
`atribuir`, `parse_geometria` de `numeracao_trecho_logradouro` sem
instanciar o `QgsProcessingAlgorithm` de lá. `CAMPO_SEQUENCIAL` e `TOL_GAP`
são novos parâmetros (o primeiro opcional, validado só quando `NUMERAR_APOS`
está marcado); não existe parâmetro de "sobrescrever" — a chamada sempre
passa por todos os `COD_LOGRADOURO` de `codigos_escopo` sem checar se já
tinham número. Testado com uma seam pesada nova: um stub completo de
`QgsProcessingAlgorithm`/`QgsVectorLayer`/`QgsFeature`/`QgsFields` (com
edição de verdade — `changeGeometry`/`changeAttributeValue`/`addFeatures`/
`deleteFeature` sobre um dicionário em memória), rodando
`RemoverTrechosPassagemAlgorithm().processAlgorithm(...)` ponta a ponta. 3
casos: cenário sintético onde um trecho X cruza (fase 0, mandatória) um
trecho de outro código Y sem nó original — a numeração encadeada só dá
números diferentes para os dois lados de X (prova de que leu a geometria
**pós**-remoção, com o nó novo já materializado) se de fato ler a camada de
novo depois da edição; controle com a opção desmarcada (SEQ intocado);
isolamento de falha (um terceiro código com gap maior que a tolerância falha
e gera aviso, sem afetar os demais)._

- [x] Parâmetro novo, desmarcado por padrão; desmarcado, nenhum número
      sequencial é tocado (comportamento idêntico a hoje)
- [x] Marcado: os `COD_LOGRADOURO` processados pela remoção/quebra são
      numerados na mesma execução, usando a geometria **pós**-remoção (não
      a original)
- [x] A numeração encadeada sempre sobrescreve a numeração anterior — sem
      nenhum parâmetro de "sobrescrever" visível na tela do algoritmo de
      remoção/quebra
- [x] Atributo de agrupamento, "apenas selecionadas" e tolerância de
      encaixe de vértices não são duplicados — a numeração encadeada
      reaproveita os mesmos valores já informados para a remoção/quebra
- [x] O algoritmo de numeração standalone (`numeracao_trecho_logradouro`)
      continua com "Sobrescrever numeração" desmarcado por padrão, sem
      nenhuma mudança de comportamento
- [x] Se a numeração falhar para um `COD_LOGRADOURO` específico (ex.: gap
      maior que a tolerância) depois que a remoção/quebra já rodou com
      sucesso para ele, a remoção/quebra permanece aplicada — o log avisa
      qual código falhou e por quê, sem interromper os demais
- [x] O código de fora dividido pela opção "Também quebrar o outro
      logradouro no cruzamento" (`.scratch/cruzamento-fora-de-escopo/`)
      nunca entra no escopo numerado por esta opção
- [x] Mensagem final do algoritmo relata as duas contagens (removidos/
      quebrados; numerados/ignorados/com falha) quando a opção está marcada
