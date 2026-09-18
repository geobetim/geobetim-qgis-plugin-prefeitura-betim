# Backend ganha um host HTTP self-hosted (`HttpListener`)

A _class library_ de numeração (ADR-0002) passa a ser exposta por um **serviço
HTTP**: um projeto console .NET Framework 4.8 que a referencia e escuta em três
rotas. O front-end deixa de falar com um _endpoint_ inexistente e passa a chamar
esse host.

## Motivação

Sem um host, não havia onde definir a connection string do Oracle nem como o
cliente exercer a numeração de verdade — o `fetch` do front batia num caminho que
nada respondia. O sistema definitivo é .NET, então o host tem que ser .NET
Framework 4.8 (a lib usa `System.Data.OracleClient` e `Lib.Data`, que não existem
fora do Framework).

## Restrições e escolhas

- **Host: `System.Net.HttpListener` self-hosted**, não ASP.NET Web API 2. Um Web
  API 2 clássico depende de pacotes NuGet via `packages.config`, e o ambiente de
  build só tem o `dotnet` SDK, que não restaura projetos `packages.config`. O
  `HttpListener` está no `System` do Framework: zero dependência a restaurar,
  compila e roda só com `dotnet build` + o `.exe`. Roteamento e serialização são
  poucas linhas escritas à mão. Se a máquina-alvo tiver MSBuild/Visual Studio
  completo, dá para trocar por um Web API 2 sem mexer nos _handlers_.
- **Prefixo `http://localhost:<porta>/`** — não exige `netsh http add urlacl`
  nem elevação (um prefixo com _host_ ou `+` exigiria).
- **JSON: Newtonsoft.Json por referência direta a DLL** (`backend/lib/`, copiada
  de `bin/`), no mesmo padrão das DLLs do NTS. Sem NuGet.
- **Três rotas**, uma operação cada:
  - `POST /api/trechos-logradouros/numerar/logradouro` — `{ codLogradouro }`
  - `POST /api/trechos-logradouros/numerar/mbr` — `{ wkt, srid }`
  - `POST /api/trechos-logradouros/codigos` — `{ logradouros: [...] }`, resposta 204
- **Resposta uniforme.** As duas rotas de numeração devolvem sempre
  `ResultadoNumeracao` (`{ logradouros, falhas }`) com HTTP 200, inclusive para um
  único logradouro: uma `NumberingException` (topologia / tolerância de
  continuação de 30 m) vira item de `falhas`, não erro HTTP. Só falha de
  infraestrutura (banco, _parse_ inesperado) devolve **HTTP 500** com
  `{ mensagem }`; JSON inválido → 400, método errado → 405, rota desconhecida →
  404.
- **DTOs de resposta dedicados** no projeto do host, com os nomes de campo que o
  cliente já lê (`IDPKTRLOGR`/`CODTRECHOLOGRADOURO` via `[JsonProperty]`, o resto
  em _camelCase_). O `NumberingService` e os modelos de domínio não mudam.
- **Configuração de conexão** em `App.config` `<appSettings>`: `Oracle.Host`,
  `Oracle.ServiceName`, `Oracle.User`, `Oracle.Password`, `Api.Port`. Cada chave
  pode ser sobreposta por uma variável de ambiente de mesmo nome; `Api.Port` cai
  para `5100`. O _composition root_ monta a connection string com
  `DatabaseAccessFactory.CreateConnectionString(DatabaseProvider.Oracle,
  string.Empty, serviceName, user, password)` — para Oracle esse método só usa
  service name, usuário e senha. `Oracle.Host` fica registrado no arquivo mas
  **não entra** nessa chamada nesta rodada (host/porta viriam de um `Data Source`
  descritor, se um dia forem necessários).
- **Só o repositório Oracle real**, sem _fake_: a API deve rodar acessando o
  Oracle.
- **ADR-0002 permanece válido** — numeração 100% automática, .NET 4.8, NTS 1.7.3
  por DLL, transformação de SRID no SQL, `SaveCodes` _no-op_. Esta rodada só
  acrescenta o transporte HTTP e a configuração; a regra de numeração não muda.

## Consequências

- Novo projeto `backend/Betim.TrechoLogradouro.Numeracao.Api/` no mesmo `.sln`
  (namespace `Betim.Logradouros.Numeracao.Api`).
- O front ganha `NUMERAR_LOGRADOURO_API_PATH` / `NUMERAR_MBR_API_PATH` e um
  _proxy_ de desenvolvimento no Vite (`/api` → `http://localhost:5100`, atrás de
  `VITE_API_PROXY=1`), no mesmo modelo do `VITE_WFS_PROXY`. Sem CORS.
- Sem testes automatizados nesta rodada; aceite é compilação da solução +
  `npm run build`/`npm test` + verificação no navegador do caminho de erro (500)
  quando o Oracle está inacessível.
- CORS na API, HTTPS, autenticação e empacotamento como serviço Windows / IIS
  ficam fora de escopo.
