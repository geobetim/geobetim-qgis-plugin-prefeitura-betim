# Domain Docs

Como as engineering skills devem consumir a documentação de domínio deste repo ao
explorar o código.

## Antes de explorar, leia

- **`CONTEXT.md`** na raiz do repo
- **`docs/adr/`**: leia os ADRs que tocam a área em que você vai trabalhar

Se algum desses arquivos não existir, **siga em silêncio**. Não sinalize a ausência;
não sugira criá-los de antemão. A skill `/domain-modeling` os cria sob demanda
quando termos ou decisões de fato são resolvidos.

## Estrutura de arquivos

Single-context (este repo):

```
/
├── CONTEXT.md
├── docs/adr/
└── remocao_trecho_logradouro_passagem/
```

## Use o vocabulário do glossário

Quando sua saída nomear um conceito de domínio (título de issue, proposta de
refactor, hipótese, nome de teste), use o termo como definido em `CONTEXT.md`. Não
derive para sinônimos que o glossário lista como `_Avoid_`.

Se o conceito que você precisa ainda não está no glossário, isso é um sinal: ou
você está inventando linguagem que o projeto não usa (reconsidere) ou há uma
lacuna real (anote para `/domain-modeling`).

## Sinalize conflitos com ADR

Se sua saída contradiz um ADR existente, exponha isso explicitamente em vez de
sobrescrever em silêncio:

> _Contradiz ADR-0007 (...), mas vale reabrir porque..._
