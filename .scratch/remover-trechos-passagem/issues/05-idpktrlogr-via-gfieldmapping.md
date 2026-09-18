# 05: `IDPKTRLOGR` dos registros novos via `GDOSYS.GFIELDMAPPING` + ADR 0005

**What to build:** quando a camada de trechos vem do Oracle escrito pelo Geomedia,
os registros novos criados pela quebra (ticket 04) recebem um `IDPKTRLOGR` de
verdade, puxado da mesma sequência que o Geomedia usa. O operador aponta qual
atributo é a chave primária; o algoritmo descobre a sequência pelo dicionário do
Geomedia e preenche. Fora desse caminho (camada não-Oracle, dicionário não
resolve), os registros novos ficam sem `IDPKTRLOGR` e o log avisa.

**Blocked by:** 04

**Status:** done

_Implementado em `sequence_geomedia.py` (`resolver_chaves`), consumido no
`algoritmo.py` após a quebra. O parâmetro `CAMPO_CHAVE_PRIMARIA` já existe desde o
ticket 04 (era usado só para zerar); aqui passou a também preencher pela
sequência. ADR `docs/adr/0005-idpktrlogr-via-gfieldmapping.md` escrito. Testado
com stub: sem parâmetro → `(-1, None, "")`; camada não-Oracle → `(idx, None,
motivo)`._

- [x] Parâmetro opcional e avançado "atributo da chave primária Geomedia
      (`IDPKTRLOGR`)" — campo da camada. Efetivo só quando
      `dataProvider().name() == "oracle"`; ignorado com aviso caso contrário.
- [x] Com o parâmetro informado e camada Oracle: `OWNER`/`TABLE_NAME` do `table`
      do data source (`QgsDataSourceUri`; qualificado `OWNER.TABELA` separado;
      senão schema do URI; senão `SYS_CONTEXT('USERENV','CURRENT_SCHEMA')`).
      `COLUMN_NAME` = campo escolhido. Os três em maiúsculas.
- [x] Consulta `SEQUENCE_OWNER`/`SEQUENCE_NAME` em `GDOSYS.GFIELDMAPPING` pela
      conexão Oracle da camada (`QgsProviderRegistry` → `providerMetadata` →
      `createConnection` → `executeSql`).
- [x] Exatamente uma linha com sequência preenchida → N próximos valores numa só
      consulta (`CONNECT BY LEVEL <= n`), atribuídos aos N registros novos.
- [x] Qualquer outro caso → registros novos com `IDPKTRLOGR` nulo e aviso no log
      com contagem/motivo; o registro novo nunca herda o `IDPKTRLOGR` do
      original.
- [x] O resumo no log informa quantos registros novos saíram com e sem
      `IDPKTRLOGR`.
- [x] `docs/adr/0005-idpktrlogr-via-gfieldmapping.md` escrito.
- [x] `python -m py_compile` limpo; teste dos fallbacks de `resolver_chaves`.
- [ ] Verificação do operador no QGIS 3.28 sobre a camada Oracle real: registros
      novos da quebra saem com `IDPKTRLOGR` da sequência; numa camada não-Oracle
      saem nulos com aviso. (pendente)
