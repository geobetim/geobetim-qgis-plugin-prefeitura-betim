# 01: Numeração automática — trecho degenerado tratado como nó de passagem

**What to build:** o `GrafoLogradouro`/`SequenciadorAutomatico` deixam de
contar as pontas de um **trecho degenerado** (trecho cujas duas pontas caem
no mesmo nó, dentro da tolerância de encaixe) no grau, na adjacência e nos
cruzamentos daquele nó — mas o mapeamento trecho→nó continua registrado. O
sequenciador nunca oferece um trecho degenerado como candidato de percurso
(não entra na pilha de bifurcação, não é visitado por retrocesso); ele é
resolvido assim que o nó em que cai é alcançado pela primeira vez (percurso
normal, salto entre componentes, ou trecho inicial), entrando na sequência
final ali mesmo, sem nunca mover a posição de referência (`_no_atual`). Como
o nó deixa de contar como cruzamento (grau real dos vizinhos), o mecanismo
já existente de atribuição de número sequencial ("nó compartilhado que não é
cruzamento → herda o número do anterior") passa a produzir o resultado
certo automaticamente, sem precisar de mudança própria. O algoritmo emite um
aviso de feedback (`IDPKTRLOGR` + `COD_LOGRADOURO`) sempre que encontra um
trecho degenerado, esteja ele dentro ou fora de um contexto de nó de
passagem — fora desse contexto (isolado, num cruzamento real, ou numa
extremidade) ele não é tocado, só avisado.

**Blocked by:** None (can start immediately)

**Status:** done

_`GrafoLogradouro.definir_alvo` passou a detectar `a == b` e guardar o id em
`self.degenerados`, sem contribuir para `graus`/`adjacencia`/`cruzamentos`
(mas `extremos_do_trecho` continua populado). `SequenciadorAutomatico`
ganhou `_pendentes_por_no` (nó → trechos degenerados pendentes) e
`_resolver_degenerados(no)`, chamado em todo ponto onde `_no_atual` é
definido (início, `_percorrer`, retrocesso de junção, `_continuar_disjunto`)
— nunca cria `Incidencia`, nunca disputa bifurcação, nunca é empilhado.
`_candidatos_de_partida` passou a operar só sobre trechos reais (exclui
degenerados de extremidades/anel fechado); `run()` trata o caso de alvo
100% degenerado (código de um só trecho) separadamente. Nenhuma mudança em
`atribuidor.py` — como o nó deixa de contar como cruzamento, o mecanismo
existente já produz o número certo. Aviso adicionado em `algoritmo.py`
(`IDPKTRLOGR` + `COD_LOGRADOURO`) depois de cada numeração bem-sucedida._

_Verificado por stub de `qgis.core` com 5 cenários sintéticos (mid-path com
salto pra componente desconexo — reproduz exatamente o padrão do 7644 real;
extremidade antes de salto; cruzamento real de 3 ramos; isolado; regressão
sem degenerado) — todos GREEN. Regressão adicional manual: eixo paralelo
(trecho desconectado legítimo) e anel fechado simples continuam produzindo a
mesma sequência de antes. `py_compile` limpo no projeto inteiro. A
verificação contra os 4 `COD_LOGRADOURO` reais (`57`, `1078`, `7644`,
`8130`) via QGIS MCP ficou pendente — a instância do QGIS ficou
inacessível no meio da sessão (parou de responder a `ping`/`diagnose` depois
de uma tentativa de `reload_plugin`); os testes sintéticos reproduzem o
padrão exato encontrado nesses códigos reais (mesma estrutura: nó interior
com self-loop entre dois vizinhos reais, seguido de salto para componente
desconexo), então a confiança na correção é alta, mas a confirmação direta
na camada real deve ser feita quando o QGIS voltar a responder._

_Code review (`/code-review --level high`) encontrou e corrigiu: aviso de
trecho degenerado ausente na numeração encadeada (`_numerar_codigos_afetados`
em `remocao_trecho_logradouro_passagem/algoritmo.py`); duplicação do laço de
aviso entre os dois algoritmos, extraída para `avisar_trechos_degenerados`
em `shared/camada.py`; detecção de trecho degenerado duplicada entre
`grafo.py` e `identificacao.py`, unificada em `IndiceDeNos.eh_degenerado`;
repetição de `_no_atual = X; _resolver_degenerados(X)` em 3 pontos do
sequenciador, unificada em `_mover_para`; ordem não determinística de
degenerados co-localizados (iteração de set), corrigida com `sorted()`; e a
direção de um trecho degenerado podendo viciar o desempate de bifurcação
quando ele é o alvo de um salto, corrigida para preservar a direção
anterior nesse caso._

- [ ] `COD_LOGRADOURO 7644` (com o trecho degenerado `IDPKTRLOGR 33792` num nó
      interno entre dois vizinhos reais) numera com sucesso, sem erro de gap;
      o trecho degenerado recebe o mesmo número sequencial do segmento
- [ ] `COD_LOGRADOURO 57`, `1078` e `8130` (reais, hoje falham com o mesmo
      padrão) numeram com sucesso depois da correção
- [ ] Trecho degenerado numa extremidade de um componente, logo antes de um
      salto para outro componente desconexo: o salto mede a distância a
      partir do vizinho real, não do self-loop
- [ ] Trecho degenerado num nó que já é cruzamento real (bifurcação de 3+
      ramos reais): não interfere na contagem de cruzamento; é resolvido e
      avisado, sem virar candidato de percurso
- [ ] Trecho degenerado isolado (único trecho do seu `COD_LOGRADOURO`, ou sem
      vizinho real por perto): numeração completa normalmente, com aviso
- [ ] Aviso de feedback citando `IDPKTRLOGR` e `COD_LOGRADOURO` emitido em
      todos os casos acima
- [ ] Regressão: um `COD_LOGRADOURO` sem nenhum trecho degenerado numera
      exatamente como antes (mesma sequência, mesmos números) — inclui os 6
      códigos reais que já passavam antes da correção
- [ ] Nenhuma mudança na semântica ou no cálculo da tolerância de continuação
      para trechos desconectados legítimos (eixo paralelo/pista dupla)
