# 03: Renomear o algoritmo

**What to build:** o algoritmo "Remover trechos de passagem" passa a se
chamar "Quebrar e remover trechos de passagem" — nome de exibição e `name()`
interno (`quebrar_remover_trechos_passagem`) — para refletir que ele também
quebra (pela própria camada e por camadas de quebra), não só remove.
`shortHelpString`, `metadata.txt` e `CONTEXT.md` sincronizados, já
descrevendo as duas capacidades novas dos tickets 01 e 02.

**Blocked by:** 02 (Quebrar o outro logradouro fora de escopo)

**Status:** done

_`class RemoverTrechosPassagemAlgorithm` mantida (nome Python interno, não
é o `name()` do Processing nem faz parte de nenhuma interface pública) —
só `name()`/`displayName()` e os textos user-facing mudaram, evitando churn
desnecessário em `provider.py`. Rótulo do comando de edição
(`edicao_sem_commit`) e docstring do módulo sincronizados também._

- [x] `displayName()` retorna "Quebrar e remover trechos de passagem"
- [x] `name()` retorna `quebrar_remover_trechos_passagem`
- [x] `shortHelpString` descreve as três fases, o parâmetro de quebrar fora
      de escopo (ticket 02) e o quase toque contra qualquer ponto (ticket
      01)
- [x] `metadata.txt` (`about=`, `version=`) sincronizado com o novo nome e
      as novas capacidades
- [x] `CONTEXT.md` ("Plugin do QGIS", "Remoção de trecho de passagem")
      atualizado com o novo nome do algoritmo
