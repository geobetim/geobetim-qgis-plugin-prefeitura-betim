# 02: Remoção de trecho de passagem — trecho degenerado absorvido no segmento

**What to build:** `_no_de_passagem` deixa de contar as pontas do próprio
**trecho degenerado** (trecho cujas duas pontas caem no mesmo nó, dentro da
tolerância de encaixe) ao decidir se um nó é nó de passagem — os dois
vizinhos reais do mesmo `COD_LOGRADOURO` voltam a formar segmento de
passagem entre si normalmente. Depois de identificados os segmentos normais
(só com trechos reais), cada trecho degenerado cujo nó caia num ponto
interno de algum desses segmentos (entre dois trechos reais consecutivos que
compartilham aquele nó) é inserido na lista ordenada, na posição entre esses
dois vizinhos. Nenhuma mudança em `colapsar`/`_estender`/`_incorporar_lado`
— o trecho degenerado é absorvido pelo mecanismo já existente (não ganha
vértice novo no trecho absorvedor, nunca é escolhido absorvedor por ser
sempre o menor). O algoritmo emite um aviso de feedback (`IDPKTRLOGR` +
`COD_LOGRADOURO`) sempre que encontra um trecho degenerado, esteja ele
dentro ou fora de um contexto de nó de passagem — fora desse contexto
(isolado, num cruzamento real, ou numa extremidade) ele não é tocado, só
avisado.

**Blocked by:** None (can start immediately)

**Status:** done

_`_no_de_passagem` ganhou o parâmetro `degenerados` e para de contar as
pontas desses trechos. `segmentos_de_passagem` continua devolvendo só
listas de trechos reais (inserir o degenerado na lista quebrava a
heurística de anel fechado do `colapsar` — ver nota abaixo); em vez disso,
nova função `trechos_degenerados_absorviveis(indice, ids_cod, cod,
nos_bloqueados)` mapeia cada degenerado aos seus vizinhos reais quando o nó
dele é nó de passagem. `algoritmo.py` chama essa função depois de
`colapsar()`: se algum vizinho do degenerado aparece no resultado (absorvido
ou apagado), o degenerado entra em `apagar_total` também — sem alteração
nenhuma em `colapsar`/`absorcao.py`. `trechos_degenerados` (antes privada)
ficou pública, reaproveitada tanto ali quanto no aviso de feedback, emitido
sempre que um `COD_LOGRADOURO` tem algum trecho degenerado, dentro ou fora
de contexto de nó de passagem._

_Nota de implementação importante: a primeira tentativa inseriu o trecho
degenerado diretamente na lista ordenada do segmento (entre os dois
vizinhos reais), mas isso quebra `colapsar`'s heurística de "segmento
fechado" (`eh_ciclo`) — ela verifica se o primeiro e o último elemento da
lista compartilham nó, e um segmento de 2 trechos reais + 1 degenerado no
meio vira 3 elementos onde essa checagem dá falso positivo (o degenerado no
meio faz o primeiro e o último trecho parecerem as duas pontas de um anel).
A abordagem final (pós-processamento depois de `colapsar`, sem tocar
`_ordenar`/`colapsar`) evita esse problema por completo e bate com a decisão
do spec de não alterar `absorcao.py`._

_Verificado por stub de `qgis.core`/`IndiceDeNos` com 4 cenários sintéticos
(degenerado num segmento de passagem — absorvido, sem vértice extra no
absorvedor; degenerado num cruzamento real de 3 ramos — não absorvido;
degenerado isolado — não absorvido; regressão sem degenerado) — todos
GREEN. Regressão adicional manual: nó tocado por outro `COD_LOGRADOURO` e nó
bloqueado por camada de quebra continuam corretamente impedindo nó de
passagem. `py_compile` limpo no projeto inteiro._

- [ ] Trecho degenerado entre dois trechos reais que formam um segmento de
      passagem: o segmento colapsa incluindo o trecho degenerado — ele
      aparece no conjunto de trechos apagados, sem ganhar vértice no trecho
      absorvedor
- [ ] Trecho degenerado num nó de cruzamento real (bifurcação de 3+ trechos,
      ou nó tocado por outro `COD_LOGRADOURO`): não entra no conjunto de
      trechos apagados; é avisado
- [ ] Trecho degenerado isolado (sem vizinho real do mesmo `COD_LOGRADOURO`
      por perto): não entra no conjunto de trechos apagados; é avisado
- [ ] Aviso de feedback citando `IDPKTRLOGR` e `COD_LOGRADOURO` emitido em
      todos os casos acima
- [ ] Regressão: um `COD_LOGRADOURO` sem nenhum trecho degenerado colapsa
      exatamente como antes (mesmos segmentos, mesmo trecho absorvedor,
      mesma geometria final)
- [ ] Nenhuma alteração em `colapsar`/`absorcao.py` — a correção fica só na
      identificação dos segmentos de passagem
