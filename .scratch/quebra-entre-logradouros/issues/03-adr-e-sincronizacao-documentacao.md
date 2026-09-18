# 03: ADR-0006 e sincronização de documentação

**What to build:** quem ler o ADR ou a spec da remoção de trecho de passagem
encontra o modelo de três fases (fase 0 nova incluída), com o trade-off da
decisão registrado. Só documentação; nenhuma mudança de comportamento.

**Blocked by:** 02

**Status:** done

_`docs/adr/0006-camada-de-trechos-fonte-obrigatoria-de-cruzamento.md` escrito.
`.scratch/remover-trechos-passagem/spec.md`: status e "Fluxo de execução"
renumerados para o modelo de três fases (fase 0 nova, índice de nós montado
só depois dela, aplicação final e resumo cobrindo id real truncado sem outra
mudança e id temporário absorvido). `metadata.txt`: `about` menciona a fase 0
e `version` 0.3.0 → 0.4.0. `CONTEXT.md` já trazia fase 0/três fases desde a
modelagem — nada a ajustar._

- [x] `docs/adr/0006`: a própria camada de trechos como fonte obrigatória de
      cruzamento na remoção de trecho de passagem — trade-off entre correção
      topológica automática (sem exigir camada de quebra configurada) e o
      custo de comparar cada trecho em escopo contra a vizinhança de outros
      códigos, mais a complexidade do identificador temporário para pedaços
      ainda não persistidos. ADR-0004 e ADR-0005 citados como ainda válidos;
      ADR-0005 reaproveitado (mesma resolução de chave), não alterado.
- [x] `.scratch/remover-trechos-passagem/spec.md`: "Fluxo de execução" e
      "Status" com o ponteiro para `.scratch/quebra-entre-logradouros/` e a
      menção ao modelo de três fases (fase 0 antes da fase 1).
- [x] Confere `metadata.txt` (`about`) e `CONTEXT.md` — o glossário
      (**Cruzamento**, **Remoção de trecho de passagem**, **Camada de
      quebra**) já foi atualizado na modelagem; só ajustar se algo ficou
      defasado depois da implementação do ticket 02.
