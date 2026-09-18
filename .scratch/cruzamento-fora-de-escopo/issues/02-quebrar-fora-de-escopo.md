# 02: Quebrar o outro logradouro fora de escopo

**What to build:** novo parâmetro booleano no algoritmo de remoção/quebra,
desmarcado por padrão: "Também quebrar o outro logradouro no cruzamento".
Desmarcado (padrão), o comportamento é o de hoje — a fase 0 nunca modifica
um `COD_LOGRADOURO` fora do escopo selecionado, só o usa como referência.
Marcado, um trecho de outro código fora de escopo que cruza um trecho em
escopo (mesma detecção da fase 0, incluindo quase toque) também é
dividido — só a divisão: o pedaço resultante não entra em colapso de
segmento de passagem (fase 1) nem em quebra por camada de quebra (fase 2)
nessa execução, e o código de fora nunca é adicionado ao conjunto
processado pelas fases 1/2. O pedaço novo do lado de fora recebe
`IDPKTRLOGR` da sequência do Geomedia, pelo mesmo pipeline já usado para os
pedaços em escopo.

Caso real de referência: rodar o algoritmo só no `COD_LOGRADOURO 7643`, com
a opção marcada, deve dividir o trecho `IDPKTRLOGR 33748` (do
`COD_LOGRADOURO 7647`, fora do escopo selecionado) no ponto onde cruza
`7643`.

**Blocked by:** None (can start immediately)

**Status:** done

_`quebrar_cruzamentos_entre_logradouros` ganhou o parâmetro
`quebrar_fora_de_escopo` (default `False`): durante o laço da fase 0,
acumula, por candidato fora de `ids_escopo`, a lista de geometrias em
escopo que o tocam (`linhas_escopo_por_cand_fora`); depois do laço
principal, corta cada um desses candidatos com
`distancias_de_intersecao_interna` (reaproveitada, sem duplicar a lógica de
dedup) e materializa os pedaços do mesmo jeito que um id em escopo — id
original vira o primeiro pedaço, id temporário novo para o resto,
`cod_novo`/`origem_real` com o código/origem do candidato de fora, nunca do
escopo. `algoritmo.py` ganhou o parâmetro
`QgsProcessingParameterBoolean` "Também quebrar o outro logradouro no
cruzamento" e só passa o valor pra frente — **nenhuma outra mudança** foi
necessária em `algoritmo.py`: o resto do pipeline (bucket por código em
`por_codigo`, fase 1 restrita a `codigos_escopo`, materialização de
`geom_nova_reais`/`temp_sobreviventes`, cópia de atributos, resolução de
chave primária) já trata todo `temp_id`/`origem_real` de forma genérica, por
código próprio — confirmado por leitura cuidadosa do código, sem exigir um
teste de integração pesado no nível do `QgsProcessingAlgorithm` completo.
Testado com stub de `qgis.core`: 4 casos (desmarcado não toca fora de
escopo; marcado divide os dois lados de um X, cada um com o código certo;
controle sem cruzamento; reprodução real do `7643`/`33748` com dados do
WFS)._

- [x] Parâmetro novo, desmarcado por padrão; com ele desmarcado, o resultado
      é idêntico ao algoritmo antes desta mudança (nenhum código fora de
      escopo tocado)
- [x] Marcado: um trecho de outro código fora de escopo que cruza um trecho
      em escopo é dividido no ponto do cruzamento
- [x] O pedaço novo do código de fora recebe `IDPKTRLOGR` da sequência do
      Geomedia (ou nulo, com aviso, fora do Oracle) — mesmo pipeline dos
      demais pedaços da fase 0
- [x] O código de fora dividido não aparece em nenhum segmento de passagem
      colapsado nem quebra de camada de quebra dessa execução, mesmo que
      teria, ele também, um segmento de passagem colapsável
- [x] Se dois códigos diferentes fora de escopo cruzarem o mesmo trecho em
      escopo em pontos distintos, ambos são divididos, cada um no seu ponto
- [x] Reprodução real: `COD_LOGRADOURO 7643` (com `33748` do `7647` como
      candidato fora de escopo), usando dados do WFS, análogo ao teste de
      regressão do `7647`/`7643` já existente
