# 09: Descarte visível, escrita checada e `COD_LOGRADOURO` nulo desconsiderado

**What to build:** o operador nunca mais termina uma execução "sem erro e sem
nada gravado" sem saber por quê. Três correções encontradas na checagem geral
dos algoritmos contra as specs:

1. **Descarte visível na numeração.** Quando todo logradouro em escopo é
   descartado por "já numerado" (0 a numerar), o log mostra um **aviso** — não
   uma linha de info — dizendo que nada foi gravado e que "Sobrescrever
   numeração" renumera. O mesmo aviso aparece quando "apenas selecionadas" está
   ligado e algum dos códigos selecionados foi descartado: o operador escolheu
   aquele logradouro à mão, o silêncio é o que dá a sensação de "não fez nada".
2. **Escrita na camada checada.** `changeAttributeValue`, `changeGeometry`,
   `addFeatures` e `deleteFeature` devolvem `bool`; hoje o retorno é ignorado e
   o resumo diz "atualizado" mesmo se o QGIS recusou. Passa a abortar com
   `QgsProcessingException` na primeira recusa (o comando de edição é
   destruído — nada fica pela metade), nos dois algoritmos.
3. **`COD_LOGRADOURO` nulo desconsiderado.** Trecho sem código de logradouro
   não entra em escopo, não entra no grafo e não conta como cruzamento, nos dois
   algoritmos. A leitura da camada avisa quantos foram desconsiderados.

E um acerto de resumo: a remoção passa a contar segmentos **de fato
colapsados** (hoje conta os identificados, inclusive os pulados por aviso).

**Blocked by:** 08

**Status:** done

_`shared/camada.py`: `ler_camada` pula feição com atributo de agrupamento nulo
(`None`/`NULL`) e devolve `sem_codigo`; `avisar_sem_codigo` emite o aviso
padrão. `shared/edicao.py`: `exigir(ok, mensagem)` levanta
`QgsProcessingException` — dentro de `edicao_sem_commit` isso destrói o comando.
Numeração: avisos de descarte (0 a numerar / selecionados ignorados), escrita
via `exigir`, mensagem de tipo do campo. Remoção: escritas via `exigir`, resumo
conta `len(geom_nova)` por logradouro (só o que colapsou). Testado com stub:
leitura com `NULL` e `None` (2 desconsiderados, fora dos dicionários e do
índice), escrita aceita (begin → change → end → repaint) e recusada (exceção
com o motivo, `destroyEditCommand`, sem `endEditCommand`). O acerto do resumo
da remoção é uma troca de contador (`len(segmentos)` → `len(geom_nova)` após o
`colapsar`) verificada por leitura, sem stub._

## Acceptance criteria

- [x] Numeração: com 0 a numerar, `pushWarning` explícito ("nada foi gravado…
      'Sobrescrever numeração'…"); com "apenas selecionadas" e algum código
      selecionado descartado, `pushWarning` listando os códigos descartados.
- [x] Numeração: `changeAttributeValue` recusado → `QgsProcessingException`
      dentro do comando de edição (comando destruído, nada gravado).
- [x] Remoção: `changeGeometry` / `addFeatures` / `deleteFeature` recusados →
      `QgsProcessingException` dentro do comando de edição.
- [x] Leitura da camada (`shared`) pula feições com valor nulo no atributo de
      agrupamento e informa a contagem; os dois algoritmos avisam no log quando
      a contagem é > 0. Trecho nulo não está no índice espacial nem no índice de
      nós — logo não é cruzamento para ninguém.
- [x] Remoção: resumo conta segmentos colapsados e logradouros com segmento a
      partir do que `colapsar` devolveu, não do que foi identificado.
- [x] Numeração: mensagem de erro do tipo do campo diz "numérico (inteiro ou
      real)"; `Double` continua aceito, o valor gravado continua `int(n)`.
- [x] `python -m py_compile` limpo; testes funcionais com stub cobrindo:
      leitura com código nulo (pulado + contagem), escrita recusada (exceção e
      `destroyEditCommand`); resumo da remoção verificado por leitura.
- [ ] Verificação do operador no QGIS 3.28: rodar a numeração num logradouro já
      numerado sem "Sobrescrever" → aviso amarelo no log. (pendente)
