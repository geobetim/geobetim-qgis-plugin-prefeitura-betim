# 02: Opção "Sobrescrever numeração" no algoritmo de numeração

**What to build:** o operador da numeração ganha um checkbox "Sobrescrever
numeração" para renumerar um `COD_LOGRADOURO` mesmo que ele já tenha o **número
sequencial do trecho** preenchido em algum trecho. Serve para reconciliar a
numeração de logradouros que tiveram a geometria alterada (por exemplo depois da
**remoção de trecho de passagem**). Desligado por padrão — o comportamento atual.

**Blocked by:** 01

**Status:** done

- [x] Novo parâmetro booleano "Sobrescrever numeração" no algoritmo de numeração,
      `defaultValue=False` (constante `SOBRESCREVER`, logo abaixo de "apenas
      selecionadas").
- [x] Desligado: comportamento idêntico ao de hoje — `not sobrescrever and
      any(seq_preenchido...)` mantém o descarte; `COD_LOGRADOURO` já numerado é
      ignorado e contado.
- [x] Ligado: a etapa de descarte por "já numerado" é pulada; todo
      `COD_LOGRADOURO` em escopo entra em `a_numerar` e o número sequencial é
      sobrescrito onde já havia valor.
- [x] Resumo coerente: com a opção ligada, `ignorados` fica em 0.
- [x] `shortHelpString` menciona a opção; `about` do `metadata.txt` já descreve
      a remoção/numeração do conjunto.
- [x] Nenhuma outra mudança de comportamento na numeração.
- [x] `python -m py_compile` limpo.
- [ ] Verificação do operador no QGIS 3.28 num `COD_LOGRADOURO` já numerado, com
      e sem a opção (pendente).
