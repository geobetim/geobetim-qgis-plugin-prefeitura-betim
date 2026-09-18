# Numeração migra para um serviço C# (.NET Framework 4.8, NTS 1.7.3)

A numeração dos trechos, que era feita no navegador em TypeScript com um fluxo
guiado por perguntas, passa a ser um **class library C#** rodando no back-end,
**100% automática** (sem intervenção humana). O front-end vira cliente fino: só
dispara a numeração (por logradouro selecionado ou pelo MBR do mapa) e exibe o
resultado.

## Motivação

O sistema definitivo é .NET e a numeração precisa rodar em lote (por MBR, milhares
de logradouros) contra o Oracle Spatial, o que o navegador não comporta. Tornar a
numeração automática elimina o fluxo guiado e a etapa de reordenação.

## Restrições e escolhas

- **Alvo:** .NET Framework 4.8, `.csproj` no formato antigo (não-SDK).
- **NetTopologySuite 1.7.3.16791** (com `GeoAPI 1.1.0.0` e `ProjNET`), por
  **referência direta a DLL** (`backend/lib/`), não NuGet — versão travada pelo
  ambiente do cliente. Namespace raiz `GisSharpBlog.NetTopologySuite`; interfaces
  em `GeoAPI.Geometries`. Sem `NearestNeighbour` — busca do mais próximo é
  varredura manual.
- **SRID:** a rotina trabalha num único SRID métrico (Oracle: 82300). A
  transformação do MBR de entrada (ex.: 4326) para 82300 é feita **no SQL**
  (`SDO_CS.TRANSFORM`); a rotina não reprojeta nada e não usa ProjNET.
- **Consulta de dados:** para cada `COD_LOGRADOURO`, uma única consulta espacial
  traz os trechos dele **mais** os de outros logradouros que intersectam a sua
  geometria (insumo para detectar cruzamento). O SQL fica pronto como comentário;
  a conexão ao Oracle é etapa posterior.
- **Regra de código:** ADR-0001 permanece — `CODTRECHOLOGRADOURO` por segmento,
  incrementa em cruzamento, herda em nó de passagem, pode repetir entre trechos.
- **Persistência:** fora de escopo agora. Há um `SaveCodes` _no-op_ ao lado das
  rotinas C#; o front continua com o botão "Salvar", que POSTa o resultado.

## Consequências

- Removido do front: `src/engine/` inteiro, `generation.ts`, `node-index.ts`, o
  fluxo guiado/reordenação e a suíte de testes do motor.
- Sem testes automatizados nesta rodada (C# e front); verificação manual.
- O front passa a depender de um endpoint `/api/trechos-logradouros/numerar` que
  ainda não tem host — mesmo padrão de stub já usado para `/codigos`.

## Emenda — 2026-09-03

Ao ligar o repositório ao Oracle de verdade (DLLs `Lib` / `Lib.Data`,
`DatabaseAccess`), quatro escolhas foram firmadas:

- **Área de numeração como WKT.** `GetStreetCodesInBoundingBox` e o overload
  público de numeração por área passam a receber `(string wkt, int srid)` em vez
  de quatro `double`. A área pode ser qualquer polígono; em geral é o retângulo da
  vista. O front monta o `POLYGON` em EPSG:4326 e envia `{ wkt, srid }`.
- **Reprojeção via `SDO_GEOMETRY(:wkt, :srid)`.** O construtor de 2 argumentos
  (Oracle 11g+) cabe numa expressão única dentro de `SDO_ANYINTERACT`. Banco
  anterior ao 11g exigiria bloco com `SDO_UTIL.FROM_WKTGEOMETRY`.
- **Credenciais na connection string (piloto).** `TrechoLogradouroRepositoryOracle`
  recebe a connection string pronta, com usuário/senha embutidos — sem
  `app.config`, sem parâmetros separados. A ligar num ambiente definitivo, trocar
  por leitura de configuração.
- **Erro de banco aborta o lote.** Exceções do provider Oracle sobem sem
  tratamento. Só `NumberingException` (topologia / tolerância de continuação de
  30 m) vira item de `Falhas` numa numeração por lista ou por área — falha de
  infraestrutura não pode se disfarçar de "logradouro não numerável".

Limite conhecido do piloto: `:wkt` é ligado como `VARCHAR2`, então WKT acima de
~4000 caracteres não funciona (irrelevante para o retângulo da vista).
