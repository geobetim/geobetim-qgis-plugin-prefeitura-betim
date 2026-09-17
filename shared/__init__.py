"""Utilidades compartilhadas entre os algoritmos do conjunto.

Regra de dependência: este pacote **não importa** de
``numeracao_trecho_logradouro`` nem de ``remocao_trecho_logradouro_passagem``.
Os algoritmos importam daqui, nunca o contrário, e nunca um do outro.

- ``topologia``: agrupa pontas de trecho em nós por uma tolerância de encaixe e
  responde, por nó, grau / `COD_LOGRADOURO` incidentes / trechos incidentes.
- ``camada``: exige CRS métrico e lê a camada inteira para estruturas em memória
  com índice espacial.
- ``edicao``: aplica mudanças no buffer de edição da camada sem ``commitChanges``.
"""
