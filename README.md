# Prefeitura de Betim — Plugin QGIS

Plugin para o QGIS (3.28+) que adiciona o provider do Processing **"Prefeitura
de Betim"**, reunindo algoritmos de geoprocessamento da Prefeitura de Betim
para edição de camadas cadastrais. Roda inteiramente sobre a camada carregada
no QGIS — sem acesso direto a Oracle ou HTTP — e grava todo resultado no
**buffer de edição** da camada: os valores ficam visíveis no mapa e só são
persistidos quando o operador salva as edições, o que permite inspecionar
antes e reverter tudo de uma vez.

## Algoritmos

Grupo **"Trecho logradouro"**, atuando sobre a camada de trechos de
logradouro (`TRECHOLOGRADOURO`):

- **Numeração de trechos de logradouro**: numera os trechos de cada
  logradouro na ordem espacial, gravando o número sequencial inteiro por
  segmento num atributo. Um logradouro já numerado é ignorado com aviso, a
  menos que "Sobrescrever numeração" esteja ligado.
- **Quebrar e remover trechos de passagem**: colapsa cada segmento de
  passagem — sequência de trechos do mesmo logradouro ligados só por nós de
  passagem — num trecho só, o maior, estendido pelos vértices dos demais. A
  própria camada de trechos é sempre usada, sem parâmetro, para dividir um
  trecho onde ele cruza qualquer outro trecho sem nó compartilhado — mesmo
  logradouro ou não, inclusive um quase toque a qualquer ponto do traçado do
  outro, dentro da tolerância de encaixe. Por padrão um código fora de
  escopo nunca é tocado; "Também quebrar o outro logradouro no cruzamento"
  divide também o trecho de fora, só nesse ponto. Camadas de quebra
  auxiliares (linha ou polígono, opcionais) bloqueiam o colapso nos nós que
  tocam e dividem qualquer trecho em escopo que cruzem no meio, com chave
  primária dos registros novos pela sequência do Geomedia em camada Oracle.
  "Numerar os trechos após a remoção/quebra" encadeia a numeração
  automática dos códigos processados, lendo a geometria já atualizada.

Trechos com código de logradouro nulo são desconsiderados por ambos os
algoritmos. Por padrão, os dois algoritmos atuam apenas sobre as feições
selecionadas — desmarque a opção correspondente para processar a camada
inteira.

## Instalação

Copie (ou crie um link simbólico) esta pasta para o diretório de plugins do
seu perfil do QGIS:

```
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\prefeitura_betim
```

e ative o plugin em **Complementos → Gerenciar e Instalar Complementos**.

Para desenvolvimento no Windows, um link de diretório evita ter que copiar os
arquivos a cada alteração:

```
mklink /d "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\prefeitura_betim" "<caminho-deste-repositório>"
```

## Licença

[GNU General Public License v3.0](LICENSE), em linha com a licença do
próprio QGIS.
