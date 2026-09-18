# 04: ADR do porte paralelo em Python

**What to build:** A decisão de portar o algoritmo de numeração para Python no
plugin, em vez de o QGIS consumir o serviço C#, fica registrada para quem chegar
depois.

**Blocked by:** 03

**Status:** done

- [x] ADR novo registrando: o plugin do QGIS reimplementa as regras da numeração automática em Python, em vez de chamar o serviço C# por HTTP; o trade-off (duas implementações da mesma regra a manter em sincronia vs. UX nativa do Processing, operação offline, sem dependência de servidor ou Oracle); e que a fonte de verdade das regras continua sendo a solução em C# — o Python deve segui-la
- [x] ADR menciona que `docs/adr/0002` (numeração automática) e o ADR da estratégia de consulta permanecem válidos — o plugin não muda regra de numeração, só a plataforma
- [x] `CONTEXT.md` já tem os termos **Número sequencial do trecho** e **Plugin do QGIS** (feito na modelagem)
- [x] Nenhuma mudança de código nesta etapa
