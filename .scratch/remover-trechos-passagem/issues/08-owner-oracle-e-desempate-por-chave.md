# 08: Owner Oracle nunca adivinhado + desempate pela chave configurada

**What to build:** duas correções encontradas testando numa cópia da
`TRECHOLOGRADOURO` (outro owner, com sequence própria mapeada no Geomedia):

1. `resolver_chaves` (`sequence_geomedia.py`) adivinhava o `OWNER` pelo
   `CURRENT_SCHEMA` da conexão quando o URI não trazia o schema. Isso resolve o
   schema do **usuário que conecta**, não o **owner da tabela desta camada** — se
   o mesmo usuário acessa produção e uma cópia de teste em owners diferentes, o
   fallback pode resolver a sequence de **outro owner** (ex.: produção), sem
   nenhum erro — o valor puxado é real, só que da sequence errada. É o que
   aconteceu: um `IDPKTRLOGR` "de sequence real" mas que não bate com a sequence
   configurada para a cópia.
2. O desempate de qual trecho é o **absorvedor** num segmento (`_maior`, em
   `absorcao.py`) usa o id interno da feição no QGIS, não o valor do atributo que
   o operador configurou como chave primária. Nos casos comuns coincidem, mas são
   conceitos diferentes — o desempate documentado ("menor `IDPKTRLOGR`") deve
   valer de verdade quando o parâmetro está preenchido.

**Blocked by:** 05, 06

**Status:** done

_`sequence_geomedia.py`: `_owner_e_tabela` passa a usar
`QgsProviderRegistry.instance().decodeUri("oracle", camada.source())` — o
decodificador do próprio provider — em vez de reconstruir/reinterpretar
`camada.source()` via `QgsDataSourceUri`; o fallback por `CURRENT_SCHEMA` foi
**removido**: sem owner/tabela, cai direto em nulo + aviso, sem nenhuma
consulta ao Oracle. `absorcao.py`: `_maior` recebe `valor_pk_por_id` opcional e
desempata por ele (com fallback pro id da feição quando falta valor);
`colapsar` recebe e propaga esse dicionário. `algoritmo.py`: lê o campo da
chave primária via `campos_extra` do `ler_camada` e monta `valor_pk_por_id`,
passado para `colapsar`. Textos de ajuda/parâmetro deixam de assumir o nome
"IDPKTRLOGR" como fixo. Testado com stub: owner/tabela corretos → resolve a
sequence certa e nunca toca `CURRENT_SCHEMA`; owner vazio → falha sem nenhuma
chamada ao Oracle; desempate com chave configurada escolhe o menor valor, com
fallback seguro quando falta valor para algum trecho._

## Acceptance criteria

- [x] `_owner_e_tabela` usa `decodeUri("oracle", ...)`, não `QgsDataSourceUri`
      sobre a string de `camada.source()`.
- [x] Sem `CURRENT_SCHEMA` em `sequence_geomedia.py` — owner/tabela vazios
      encerram a resolução (nulo + aviso) antes de qualquer consulta Oracle.
- [x] `_maior(ids, geom_por_id, valor_pk_por_id=None)`: desempate pelo menor
      valor de `valor_pk_por_id[t]` quando presente; cai no id da feição quando
      ausente ou não numérico.
- [x] `colapsar(..., valor_pk_por_id=None)` propaga o dicionário pra `_maior`.
- [x] `algoritmo.py` lê o campo da chave primária (quando informado e existente
      na camada) via `campos_extra` do `ler_camada`, monta `valor_pk_por_id` e
      passa pra `colapsar`.
- [x] Parâmetro/ajuda deixam de tratar "IDPKTRLOGR" como nome fixo — mencionam
      como exemplo, não obrigação.
- [x] `python -m py_compile` limpo; testes funcionais cobrindo os 3 cenários do
      owner (resolve certo / falha sem tocar o Oracle / provider não-Oracle) e os
      3 do desempate (sem chave / com chave / chave parcial).
- [ ] Verificação do operador: rodar contra a cópia de outro owner e confirmar
      que o `IDPKTRLOGR` do registro novo vem da sequence **da cópia**, não da de
      produção. (pendente)
