# Issue tracker: Local Markdown

Issues e specs deste repositório vivem como arquivos markdown em `.scratch/`.

## Convenções

- Uma feature por diretório: `.scratch/<feature-slug>/`
- O spec é `.scratch/<feature-slug>/spec.md`
- Tickets de implementação são um arquivo por ticket em
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numerados a partir de `01`,
  nunca um único arquivo combinado
- Estado de triagem é registrado numa linha `Status:` no topo de cada arquivo
- Comentários e histórico de conversa vão para o fim do arquivo, sob `## Comments`

## Quando uma skill disser "publish to the issue tracker"

Criar um novo arquivo em `.scratch/<feature-slug>/` (criando o diretório se preciso).

## Quando uma skill disser "fetch the relevant ticket"

Ler o arquivo no caminho referenciado. Normalmente o usuário passa o caminho ou o
número diretamente.
