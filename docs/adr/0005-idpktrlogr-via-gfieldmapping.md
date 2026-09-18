# `IDPKTRLOGR` de trechos novos pela sequência do Geomedia (`GDOSYS.GFIELDMAPPING`)

O algoritmo "Remover trechos de passagem" pode criar registros novos ao quebrar um
**trecho absorvedor** pelas **camadas de quebra**. Quando a camada de trechos é do
provider Oracle, esses registros recebem um `IDPKTRLOGR` puxado da **mesma
sequência que o Geomedia usa**, descoberta pelo dicionário interno do Geomedia:
a tabela `GDOSYS.GFIELDMAPPING`, filtrada por `OWNER` / `TABLE_NAME` /
`COLUMN_NAME`, cujas colunas `SEQUENCE_OWNER` / `SEQUENCE_NAME` apontam a
sequência. O algoritmo então executa `SELECT "<owner>"."<seq>".NEXTVAL FROM DUAL
CONNECT BY LEVEL <= :n` pela conexão Oracle da própria camada e distribui os
valores aos registros novos.

## Motivação

O `IDPKTRLOGR` é a chave primária dos trechos e é preenchido pelo Geomedia a
partir de uma sequência do Oracle — não por trigger nem por `DEFAULT` da coluna,
mas pela aplicação. Um trecho criado fora do Geomedia (aqui, pelo QGIS) precisa
de um `IDPKTRLOGR` válido para ser gravável; sem isso o commit da camada quebra
na constraint de chave primária / not null.

O QGIS não tem como chamar o Geomedia. As alternativas consideradas:

- **Deixar `IDPKTRLOGR` nulo** e o operador resolve depois — o commit falha antes
  disso; inviável como caminho único.
- **`max(IDPKTRLOGR) + 1` local** — colide com o próximo valor real da sequência e
  com outro usuário gerando trechos ao mesmo tempo; corrompe a numeração da
  chave.
- **Ler a sequência do dicionário do Geomedia (`GDOSYS.GFIELDMAPPING`) e usar
  `NEXTVAL`** — é exatamente o que o Geomedia faria; não colide, respeita
  concorrência (o Oracle serializa `NEXTVAL`).

## Escolha

- Um parâmetro opcional e avançado aponta qual campo é a chave primária. Ele só
  tem efeito quando `dataProvider().name() == "oracle"`; em qualquer outro caso o
  parâmetro é ignorado com aviso.
- `OWNER` e `TABLE_NAME` vêm do data source da camada decodificado pelo
  **próprio provider Oracle** (`decodeUri`). **Nunca são adivinhados** — não há
  fallback pelo schema corrente da sessão: esse schema é o do usuário que
  conecta, não o owner da tabela desta camada, e o mesmo usuário costuma
  enxergar produção e uma cópia de teste em owners diferentes; adivinhar
  arriscaria resolver a sequência de **outro** owner (real, mas errada). Sem
  owner/tabela determináveis, a chave fica nula com aviso. `COLUMN_NAME` é o
  campo escolhido. Comparados em maiúsculas.
- Só se resolve a sequência quando `GDOSYS.GFIELDMAPPING` devolve **exatamente uma
  linha** com `SEQUENCE_OWNER` e `SEQUENCE_NAME` preenchidos. Zero ou várias
  linhas, colunas nulas, camada não-Oracle, falha de conexão → os registros novos
  ficam com `IDPKTRLOGR` **nulo** e um aviso no log com a contagem e o motivo. O
  registro novo **nunca** herda o `IDPKTRLOGR` do trecho original.
- Os N valores são obtidos numa única consulta (`CONNECT BY LEVEL <= n`).
- O `NEXTVAL` é consumido no momento da execução do algoritmo — antes do commit,
  já no buffer de edição. É coerente com o modelo "edição sem commit" (o operador
  revisa e pode reverter). Uma reversão deixa buracos na sequência, o que é
  aceitável e esperado no Oracle. Nem todo buraco é nosso: `LAST_NUMBER` em
  `ALL_SEQUENCES`/`USER_SEQUENCES` mostra o topo do bloco reservado em **cache**
  pelo Oracle, não o último valor emitido — um `NEXTVAL` legítimo pode vir bem
  abaixo dele depois de reinício/reconexão, sem nenhum bug envolvido.

## Consequências

- O plugin passa a depender do esquema interno do Geomedia (`GDOSYS`,
  `GFIELDMAPPING`, `SEQUENCE_OWNER`/`SEQUENCE_NAME`). Se o Geomedia mudar esse
  dicionário, a resolução para de funcionar e cai no fallback (nulo + aviso) — não
  quebra a operação, só deixa a chave para o operador.
- A consulta de dicionário monta SQL com literais (owner/table/column em
  maiúsculas, aspas simples escapadas), porque a API de conexão do provider não
  aceita bind params. Os valores vêm do URI da camada e de um nome de campo, não
  de entrada livre.
- Sem suíte de testes no repositório para esse caminho — depende de um Oracle vivo
  com o dicionário do Geomedia. Verificação = o operador rodando a quebra sobre a
  camada Oracle real e conferindo o `IDPKTRLOGR` dos registros novos; numa camada
  não-Oracle, conferindo que saem nulos com aviso.
- ADR-0002/0003/0004 permanecem válidos.
