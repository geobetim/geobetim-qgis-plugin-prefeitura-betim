# Spec: Reorganizar o projeto — plugin como raiz

**Status:** implementado

O repositório `F:/projetos/editor_trechologradouro` hoje mistura o plugin
QGIS (`plugin-qgis/prefeitura_betim/`, com seu próprio git e remoto no
GitHub) com um front-end web (`src/`, Vite/TypeScript) e um back-end .NET
(`backend/`) que não são mais o foco do projeto. O usuário confirmou backup
externo do projeto inteiro e autorizou remoção definitiva do que não for
relacionado ao plugin.

## Problem Statement

Manter código de um front-end e back-end que não são mais desenvolvidos
junto do plugin QGIS confunde onde o trabalho real acontece — o plugin tem
seu próprio git e remoto (GitHub), mas vive numa subpasta dentro de um
projeto sem controle de versão, com documentação de domínio (`CONTEXT.md`,
`docs/adr/`) e specs (`.scratch/`) espalhadas descrevendo componentes que
vão deixar de existir.

## Solution

O diretório do plugin (`plugin-qgis/prefeitura_betim/`, incluindo seu
`.git`) passa a **ser** a raiz do projeto (`F:/projetos/editor_trechologradouro`)
— sem mais aninhamento. Tudo que não é relacionado ao plugin (front-end web,
back-end .NET, binários, configuração de build do front-end) é removido.
`CONTEXT.md`, `docs/adr/` e as pastas de `.scratch/` relacionadas ao plugin
se mudam para a nova raiz (passam a ser rastreadas pelo git do plugin); o
que só descreve o front-end/back-end é removido junto.

## User Stories

1. Como mantenedor, quero que `F:/projetos/editor_trechologradouro` seja,
   ele mesmo, o diretório do plugin (o que hoje é
   `plugin-qgis/prefeitura_betim/`), para não ter mais um nível de pasta
   sem propósito.
2. Como mantenedor, quero que o `.git` e o histórico de commits do plugin
   (já publicado em `github.com/geobetim/geobetim-qgis-plugin-prefeitura-betim`)
   sejam preservados intactos depois da mudança — mesmos commits, mesmo
   remoto, só a árvore de trabalho movida.
3. Como mantenedor, quero que `CONTEXT.md` e `docs/adr/` se mudem para a
   nova raiz e passem a ser rastreados pelo mesmo git do plugin — hoje eles
   não têm controle de versão nenhum.
4. Como mantenedor, quero que `CONTEXT.md` pare de descrever o front-end web
   e o back-end (Ferramenta web, MBR, Serviço de numeração, Numeração
   automática do back-end, Logradouro totalmente contido, Sequência de
   trechos como conceito do back-end) — só os termos que o plugin usa
   continuam.
5. Como mantenedor, quero que as pastas de `.scratch/` sobre o front-end/
   back-end (`backend-api`, `codigo-por-segmento`, `editor-trechos-logradouro`,
   `numeracao-em-lote`, `numeracao-no-backend`, `repositorio-oracle`) sejam
   removidas, e as do plugin (`plugin-qgis`, `quebra-entre-logradouros`,
   `quase-toque-cruzamento`, `remover-trechos-passagem`, `segmento-fechado`,
   e as três novas desta rodada) se mudem para a nova raiz.
6. Como mantenedor, quero que o front-end (`src/`, `index.html`,
   `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts`,
   `dist/`, `run-frontend.bat`), o back-end (`backend/`, `bin/`,
   `run-api.bat`) e arquivos exclusivos deles (`.env.example`, `DESIGN.md` —
   tokens de design da interface web) sejam removidos por completo.
7. Como mantenedor, quero que `.claude/launch.json` pare de referenciar os
   servidores de desenvolvimento do front-end/back-end (não existe mais
   nada para rodar como servidor local neste projeto).
8. Como mantenedor, quero que `CLAUDE.md` descreva o projeto como o plugin
   QGIS, não como "ferramenta web local".
9. Como mantenedor, quero rodar `py_compile` em todos os módulos Python do
   plugin depois da mudança e confirmar que nenhum import relativo quebrou,
   para saber que a reorganização não alterou nenhum caminho de módulo
   Python (só a posição da pasta raiz no disco).
10. Como mantenedor, quero que o link de desenvolvimento do QGIS (`mklink`
    documentado no `README.md` do plugin) continue apontando para um
    caminho válido depois da mudança, sem precisar refazer o link se eu já
    tiver um apontando para o caminho antigo — ou receber instrução clara de
    refazê-lo.
11. Como mantenedor, quero que o commit que aplica essa reorganização no
    git do plugin deixe claro, na mensagem, que a pasta raiz do repositório
    passou a coincidir com a raiz do projeto no disco.

## Implementation Decisions

- Mecânica da mudança: mover o **conteúdo** de
  `plugin-qgis/prefeitura_betim/` (incluindo `.git/`) para
  `F:/projetos/editor_trechologradouro/`, depois remover a pasta
  `plugin-qgis/` (agora vazia); mover `CONTEXT.md` e `docs/adr/` da raiz
  antiga para a nova raiz (mesmo caminho relativo dentro dela);
  mover/filtrar `.scratch/` conforme a lista de pastas a manter; remover
  tudo o mais listado nas user stories 6-7.
- `git status`/`git add`/`git commit` na nova raiz depois da mudança: os
  arquivos que entram por trás da mudança (`CONTEXT.md`, `docs/adr/`,
  `.scratch/`) aparecem como novos para o git do plugin (nunca estiveram
  sob esse `.git` antes) — um commit só, deixando claro no corpo da mensagem
  que é a reorganização, não uma mudança de comportamento do plugin.
- `CONTEXT.md`: revisão indo entrada por entrada — mantém as que o plugin
  usa (`Trecho-logradouro`, `Logradouro`, `IDPKTRLOGR`, `COD_LOGRADOURO`,
  `CODTRECHOLOGRADOURO`, `Número sequencial do trecho`, `Extremidade`,
  `Trecho inicial`, `Nó`, `Logradouro conectado-simples`, `Bifurcação`,
  `Cruzamento`, `Nó de passagem`, `Segmento`, `Segmento de passagem`,
  `Trecho de passagem`, `Trecho absorvedor`, `Trecho desconectado`,
  `Tolerância de continuação`, `Plugin do QGIS`, `Remoção de trecho de
  passagem`, `Camada de quebra`, `Sobrescrever numeração`, `Numeração
  automática` — a definição do algoritmo do plugin, não a do back-end);
  remove ou reescreve as que só existem para o front-end/back-end (`MBR`,
  `Logradouro totalmente contido`, `Serviço de numeração` — a API HTTP).
  Onde uma entrada mistura os dois (ex.: "Numeração automática" tinha uma
  versão de back-end e é também usada pelo plugin), mantém só a parte que
  descreve o comportamento do plugin.
- `docs/adr/`: nenhum ADR precisa mudar de conteúdo — todos (0001-0007) já
  são sobre decisões técnicas que incluem ou tocam o plugin; só o ADR-0002
  (numeração no back-end em C#) e o ADR-0003 (API HTTP self-hosted) passam a
  descrever uma decisão sobre um componente que não existe mais no repo —
  mantidos como registro histórico (ADR não se edita depois de aceito), sem
  edição de conteúdo.
- `docs/agents/domain.md`: ajustar o exemplo de árvore de arquivos (hoje
  mostra `src/`) para refletir a nova raiz.
- `CLAUDE.md`: reescrever o parágrafo de abertura para descrever o plugin
  QGIS "Prefeitura de Betim", não a "ferramenta web local".
- `.claude/launch.json`: remover as configurações `dev` (Vite) e `api`
  (.NET) — não sobra nenhum servidor local para rodar; se o arquivo ficar
  sem nenhuma configuração útil, removê-lo por completo.
- `README.md` do plugin: revisar a instrução de `mklink` (o caminho de
  origem cita o path atual dentro de `plugin-qgis/prefeitura_betim/`) para
  o novo caminho (a própria raiz do projeto).

## Testing Decisions

- Não há comportamento de algoritmo para testar — a verificação é
  estrutural: `py_compile` recursivo em todos os `.py` do projeto depois da
  mudança (sem erro de import); `git status` limpo depois do commit (nada
  esquecido fora do índice, nada da pasta antiga sobrando); reexecução da
  suíte de stub já usada nas rodadas anteriores (garante que os testes
  continuam encontrando os módulos pelo mesmo caminho relativo dentro do
  pacote `prefeitura_betim`, já que a mudança não altera a estrutura
  *interna* do pacote, só onde ele mora no disco).
- Conferir manualmente (não por teste automatizado) que `github.com/geobetim/
  geobetim-qgis-plugin-prefeitura-betim` continua acessível e com o mesmo
  remoto configurado depois da mudança, antes de fazer push do commit da
  reorganização.

## Out of Scope

- Qualquer mudança de comportamento do plugin — este spec é só estrutura de
  pastas e documentação.
- Recriar ou migrar o front-end/back-end para outro lugar — são removidos,
  não movidos (o usuário já tem backup externo do estado atual).
- Renomear o repositório no GitHub — fora de escopo, a menos que pedido
  depois.

## Further Notes

- Pré-condição já confirmada pelo usuário: existe um backup externo do
  projeto inteiro antes desta remoção — a remoção é definitiva no disco
  local, sem `git` cobrindo o que está fora de `plugin-qgis/prefeitura_betim/`
  hoje.
- Esta reorganização deveria rodar **depois** de `.scratch/cruzamento-fora-de-escopo/`
  e `.scratch/numeracao-apos-remocao/` estarem implementados — mover a
  árvore de trabalho no meio de outro trabalho em andamento só aumenta o
  risco de confundir caminhos abertos/relativos durante a implementação
  deles. Ordem sugerida: implementar os outros dois specs primeiro, comitar,
  e só então reorganizar.
