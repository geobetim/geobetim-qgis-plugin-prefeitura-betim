# 10: Sincronizar documentação com os tickets 06–09

**What to build:** quem ler a spec, o ADR ou o `metadata.txt` encontra o
comportamento que o plugin tem hoje, não o de antes dos tickets 06–09. Só
documentação; nenhuma mudança de comportamento.

**Blocked by:** 09

**Status:** done

## Acceptance criteria

- [x] ADR-0005: `OWNER`/`TABLE_NAME` vêm do `decodeUri` do provider Oracle;
      **sem** fallback pelo schema da sessão — sem owner/tabela, chave nula com
      aviso. Nota sobre `LAST_NUMBER` × cache da sequence.
- [x] Spec da remoção — "Fluxo de execução": item 7 (fase 2 sobre **todo**
      trecho em escopo, polígono pela borda) e item 8 (owner nunca adivinhado)
      atualizados; itens 9–11 cobrem escrita checada, resumo real e código
      nulo; "Out of Scope" deixa de dizer "quebrar trechos que não foram
      estendidos"; status cita 09 e 10.
- [x] Spec da numeração (`.scratch/plugin-qgis/spec.md`) e ticket 02 dela:
      campo do número sequencial é **numérico** (inteiro ou real — grava-se o
      inteiro), não "recusa real"; regra de descarte descreve o aviso do ticket
      09; `COD_LOGRADOURO` nulo desconsiderado; escrita checada.
- [x] `metadata.txt` → `about` descreve o colapso por **segmento de passagem**
      e a quebra de qualquer trecho em escopo; `version` 0.2.0 → 0.3.0.
- [x] `readme.txt` → `mklink` aponta para `prefeitura_betim`.
- [x] `CONTEXT.md` já traz `COD_LOGRADOURO` nulo desconsiderado (feito na
      modelagem); os demais termos conferem com o código dos tickets 06–09.
