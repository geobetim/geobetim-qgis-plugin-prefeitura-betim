"""Chave primária dos registros novos, pela sequência do Geomedia.

O ``IDPKTRLOGR`` é preenchido pelo Geomedia a partir de uma sequência do Oracle,
registrada no dicionário ``GDOSYS.GFIELDMAPPING``. Quando a camada de trechos é
do provider Oracle e o operador aponta qual campo é essa chave, o algoritmo
resolve a sequência por esse dicionário e puxa os próximos valores para os
registros criados na quebra. Fora desse caminho, os registros novos ficam com o
campo nulo.

Consumir ``NEXTVAL`` aqui (na execução, antes do commit) é intencional: mantém o
modelo "edição sem commit" e os valores ficam visíveis/revertíveis. Buracos na
sequência por uma reversão são aceitáveis no Oracle — e nem todo "buraco" é
nosso: ``ALL_SEQUENCES``/``USER_SEQUENCES.LAST_NUMBER`` mostra o topo do bloco
já **reservado em cache** pelo Oracle, não o último valor de fato emitido por
``NEXTVAL``. Cada evento que descarta o cache em uso (reinício de instância,
reconexão) deixa esse "topo" mais à frente do que foi realmente emitido — um
`NEXTVAL` legítimo pode devolver um valor bem menor que o `LAST_NUMBER`
consultado no dicionário, sem nenhum bug envolvido.

O ``OWNER``/``TABLE_NAME`` usados na consulta a ``GDOSYS.GFIELDMAPPING`` vêm do
``decodeUri`` do próprio provider Oracle — nunca são adivinhados a partir do
schema da conexão. O usuário que conecta a camada pode ter acesso a mais de uma
tabela chamada igual em owners diferentes (produção e uma cópia de teste, por
exemplo); adivinhar o owner arriscaria resolver a sequência de OUTRO owner —
real, mas errada. Sem conseguir determinar o owner/tabela, o campo fica nulo com
aviso, em vez de arriscar.
"""

from qgis.core import QgsDataSourceUri, QgsProviderRegistry


def _owner_e_tabela(camada):
    """`(OWNER, TABLE_NAME)` em maiúsculas, decodificados pelo próprio provider
    Oracle (``decodeUri``) — não reconstrói a URI reinterpretando a string de
    ``camada.source()``, que pode não trazer o schema em todo caso."""
    partes = QgsProviderRegistry.instance().decodeUri("oracle", camada.source())
    owner = str(partes.get("schema") or "").strip().strip('"')
    tabela = str(partes.get("table") or "").strip().strip('"')
    if "." in tabela and not owner:
        owner, tabela = (p.strip().strip('"') for p in tabela.split(".", 1))
    return owner.upper(), tabela.upper()


def _conexao_oracle(camada):
    md = QgsProviderRegistry.instance().providerMetadata("oracle")
    uri = QgsDataSourceUri(camada.source())
    return md.createConnection(uri.connectionInfo(True), {})


def _lit(valor):
    return "'" + str(valor).replace("'", "''") + "'"


def resolver_chaves(camada, nome_campo_pk, quantidade):
    """Resolve ``quantidade`` valores de chave primária para registros novos.

    Devolve ``(idx_campo, valores, motivo)``:

    - ``idx_campo`` — índice do campo da chave primária, ou ``-1`` se o parâmetro
      não foi informado / o campo não existe (nesse caso os registros novos
      copiam todos os atributos do original, sem tocar na chave);
    - ``valores`` — lista com ``quantidade`` valores da sequência, ou ``None``;
    - ``motivo`` — quando ``valores is None`` e ``idx_campo >= 0``, o texto do
      aviso a mostrar no log.
    """
    if not nome_campo_pk:
        return -1, None, ""

    idx = camada.fields().indexFromName(nome_campo_pk)
    if idx < 0:
        return -1, None, ""

    if camada.dataProvider().name() != "oracle":
        return idx, None, (
            "a camada não é do provider Oracle; IDPKTRLOGR dos registros novos "
            "fica nulo."
        )

    try:
        owner, tabela = _owner_e_tabela(camada)
        coluna = nome_campo_pk.upper()
        if not owner or not tabela:
            # Nunca adivinha o owner (ex.: pelo schema da conexão) — camadas de
            # produção e de cópias de teste costumam estar acessíveis ao mesmo
            # usuário, em owners diferentes; adivinhar arrisca resolver a
            # sequence de OUTRO owner.
            return idx, None, (
                "não foi possível determinar o owner/tabela da camada pela "
                "conexão Oracle; IDPKTRLOGR dos registros novos fica nulo."
            )

        conn = _conexao_oracle(camada)
        mapa = conn.executeSql(
            "SELECT SEQUENCE_OWNER, SEQUENCE_NAME FROM GDOSYS.GFIELDMAPPING "
            "WHERE OWNER = {0} AND TABLE_NAME = {1} AND COLUMN_NAME = {2}".format(
                _lit(owner), _lit(tabela), _lit(coluna)
            )
        )
        if len(mapa) != 1:
            return idx, None, (
                "GDOSYS.GFIELDMAPPING retornou {0} linha(s) para {1}.{2}.{3}; "
                "IDPKTRLOGR dos registros novos fica nulo."
            ).format(len(mapa), owner, tabela, coluna)

        seq_owner, seq_name = mapa[0][0], mapa[0][1]
        if not seq_owner or not seq_name:
            return idx, None, (
                "sem SEQUENCE_OWNER/SEQUENCE_NAME no dicionário para "
                "{0}.{1}.{2}; IDPKTRLOGR dos registros novos fica nulo."
            ).format(owner, tabela, coluna)

        linhas = conn.executeSql(
            'SELECT "{0}"."{1}".NEXTVAL FROM DUAL CONNECT BY LEVEL <= {2}'.format(
                str(seq_owner).replace('"', ""),
                str(seq_name).replace('"', ""),
                int(quantidade),
            )
        )
        valores = [linha[0] for linha in linhas]
        if len(valores) < quantidade:
            valores += [None] * (quantidade - len(valores))
        return idx, valores, ""
    except Exception as e:  # noqa: BLE001 — qualquer falha aqui vira aviso, não erro
        return idx, None, (
            "falha ao resolver a sequência do IDPKTRLOGR ({0}); os registros "
            "novos ficam com o campo nulo."
        ).format(e)
