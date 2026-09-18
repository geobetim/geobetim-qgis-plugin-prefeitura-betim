# 03: ADR e sincronização de documentação

**What to build:** Documenta a reversão da regra de "cruzamento atípico" do
ADR-0006 e o achado de robustez numérica que a motivou — uma revisão do
próprio ADR-0006 (seção de revisão, com data e motivo) ou um ADR novo,
conforme o que ficar mais claro para quem ler depois. `CONTEXT.md`
("Cruzamento", "Remoção de trecho de passagem") deixa de mencionar
"atípico... só gera aviso" para o mesmo `COD_LOGRADOURO` — o texto passa a
descrever um único comportamento (divide sempre, mesmo código ou não).
`metadata.txt` do plugin recebe a versão incrementada e o `about=` ajustado
para não prometer mais o comportamento antigo.

**Blocked by:** 02 (Revogar o "cruzamento atípico" do mesmo COD_LOGRADOURO)

**Status:** done

_Optei por um ADR novo (0007) em vez de revisar o 0006 no lugar — o 0006
continua sendo o registro fiel de quando/por que a fase 0 nasceu; o 0007
registra a reversão específica e o achado de robustez que a motivou,
com referência cruzada entre os dois._

- [x] ADR-0007 (novo) registra a reversão da regra de "atípico", com a
      motivação (caso real do `7640` + achado de robustez numérica na
      checagem da camada inteira — 208 pares, 173 entre códigos diferentes)
- [x] `CONTEXT.md`: entrada de "Remoção de trecho de passagem" (fase 0) não
      menciona mais a exceção do mesmo `COD_LOGRADOURO`; aponta para o
      ADR-0007
- [x] `metadata.txt`: `version=0.5.0`; `about=` sincronizado (cruzamento
      contra qualquer trecho, não só "outro logradouro")
- [x] `shortHelpString`/docstring de `algoritmo.py` e `quebra_entre_logradouros.py`
      sincronizados (mesmo texto que o `about=`)
- [x] `.scratch/quebra-entre-logradouros/spec.md` e
      `.scratch/remover-trechos-passagem/spec.md` receberam uma nota
      apontando para o ADR-0007
